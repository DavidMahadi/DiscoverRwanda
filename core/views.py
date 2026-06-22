from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.core.mail import EmailMultiAlternatives
from django.template.loader import get_template
from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.views.decorators.http import require_http_methods, require_POST
from django.views.generic import ListView, DetailView
from django.utils import timezone
from django.db.models import Count, Sum, Q
from datetime import date, timedelta
import io
import json

from xhtml2pdf import pisa

from .models import TravelBooking
from .forms import TravelBookingForm


# ────────────────────────────────────────────────────────────
# PUBLIC PAGES
# ────────────────────────────────────────────────────────────

def index(request):
    return render(request, "index.html")

def towns(request):
    return render(request, 'towns.html')

def lakes(request):
    return render(request, "lakes.html")

def volcanic_mountains(request):
    return render(request, "volcanic_mountains.html")

def museums_heritage(request):
    return render(request, "museums_heritage.html")

def memorial_sites(request):
    return render(request, "memorial_sites.html")

def cultural_villages(request):
    return render(request, "cultural_villages.html")

def top_attractions(request):
    return render(request, "top_attractions.html")

def unique_experiences(request):
    return render(request, "unique_experiences.html")

def things_to_do(request):
    return render(request, "things_to_do.html")

def travel_types(request):
    return render(request, "travel_types.html")

def traveling_with_pets(request):
    return render(request, "traveling_with_pets.html")

def senior_friendly(request):
    return render(request, "senior_friendly.html")

def invest_rwanda(request):
    return render(request, "invest_rwanda.html")

def accessible_travel(request):
    return render(request, "accessible_travel.html")

def gallery(request):
    return render(request, "gallery.html")

def success(request):
    """Success page after booking form submission"""
    return render(request, 'success.html')


# ────────────────────────────────────────────────────────────
# BOOKING FORM (PUBLIC)
# ────────────────────────────────────────────────────────────

def contact_form_view(request):
    """
    Main booking form. Handles step-by-step submission.
    All data is saved exactly as the client filled it.
    """
    if request.method == 'POST':
        form = TravelBookingForm(request.POST)

        if form.is_valid():
            booking = form.save()

            # Send confirmation email to customer (accurate data from DB)
            try:
                send_customer_confirmation(booking)
            except Exception as e:
                print(f"Error sending customer email: {e}")

            # Send notification email to admin
            try:
                send_admin_notification(booking)
            except Exception as e:
                print(f"Error sending admin email: {e}")

            messages.success(
                request,
                f'Thank you {booking.first_name}! Your booking request has been received. '
                "We'll get back to you within 24 hours with a personalised itinerary."
            )
            return redirect('success')
        else:
            messages.error(
                request,
                'There were some errors in your submission. Please check the form and try again.'
            )
    else:
        form = TravelBookingForm()

    return render(request, 'contact.html', {'form': form})


# ────────────────────────────────────────────────────────────
# EMAIL HELPERS
# Activity display names — single source of truth
# ────────────────────────────────────────────────────────────

ACTIVITY_LABELS = {
    'gorilla-trekking': 'Gorilla Trekking',
    'golden-monkey': 'Golden Monkey Tracking',
    'chimpanzee': 'Chimpanzee Trekking',
    'big-five': 'Big Five Safari',
    'boat-safari': 'Boat Safari',
    'bird-watching': 'Bird Watching',
    'canopy-walk': 'Canopy Walk',
    'guided-walks': 'Guided Nature Walks',
    'waterfall-hikes': 'Waterfall Hikes',
    'volcano-hiking': 'Volcano Hiking',
    'mountain-climbing': 'Mountain Climbing',
    'kayaking': 'Kayaking',
    'congo-nile': 'Congo Nile Trail',
    'sport-fishing': 'Sport Fishing',
    'zip-lining': 'Zip Lining',
    'sunset-cruise': 'Sunset Cruise',
    'swimming-beach': 'Swimming & Beach',
    'spa-wellness': 'Spa & Wellness',
    'yoga-meditation': 'Yoga & Meditation',
    'hot-springs': 'Hot Springs',
    'golf': 'Golf',
    'genocide-memorial': 'Genocide Memorial',
    'cultural-villages': 'Cultural Villages',
    'traditional-dance': 'Traditional Dance',
    'cooking-classes': 'Cooking Classes',
    'art-workshops': 'Art Workshops',
    'museums-galleries': 'Museums & Galleries',
    'coffee-tours': 'Coffee Tours',
    'tea-plantations': 'Tea Plantations',
    'market-tours': 'Market Tours',
    'kigali-tour': 'Kigali City Tour',
    'fine-dining': 'Fine Dining',
    'street-food': 'Street Food Tours',
    'nightlife-music': 'Nightlife & Music',
    'photography-tours': 'Photography Tours',
    'shopping': 'Shopping',
}

ACTIVITY_CATEGORIES = {
    '🦍 Wildlife & Primates': ['gorilla-trekking', 'golden-monkey', 'chimpanzee'],
    '🦁 Safari Experiences': ['big-five', 'boat-safari', 'bird-watching'],
    '🌿 Nature & Adventure': ['canopy-walk', 'guided-walks', 'waterfall-hikes', 'volcano-hiking', 'mountain-climbing'],
    '🏖️ Lake Kivu Activities': ['kayaking', 'congo-nile', 'sport-fishing', 'zip-lining', 'sunset-cruise',
                                 'swimming-beach', 'spa-wellness', 'yoga-meditation', 'hot-springs', 'golf'],
    '🎭 Cultural Experiences': ['genocide-memorial', 'cultural-villages', 'traditional-dance',
                                 'cooking-classes', 'art-workshops', 'museums-galleries',
                                 'coffee-tours', 'tea-plantations', 'market-tours'],
    '🏙️ Kigali City': ['kigali-tour', 'fine-dining', 'street-food', 'nightlife-music',
                        'photography-tours', 'shopping'],
}


def _build_activities_html_for_customer(activities):
    """Build categorised activities HTML block for customer email."""
    html = ''
    for category, keys in ACTIVITY_CATEGORIES.items():
        matched = [ACTIVITY_LABELS.get(k, k.replace('-', ' ').title()) for k in keys if k in activities]
        if matched:
            html += (
                f'<div style="margin-bottom:18px;">'
                f'<div style="font-weight:700;color:#111;font-size:14px;margin-bottom:8px;">{category}</div>'
            )
            for name in matched:
                html += f'<div style="padding:5px 0;color:#555;font-size:14px;">• {name}</div>'
            html += '</div>'
    return html or '<div style="color:#666;font-style:italic;">To be discussed during planning</div>'


def _build_activities_html_for_admin(activities):
    """Build categorised activities HTML block for admin email."""
    html = ''
    for category, keys in ACTIVITY_CATEGORIES.items():
        matched = [ACTIVITY_LABELS.get(k, k.replace('-', ' ').title()) for k in keys if k in activities]
        if matched:
            html += (
                f'<div style="margin-bottom:14px;">'
                f'<strong style="color:#000;font-size:13px;">{category}</strong>'
            )
            for name in matched:
                html += f'<div style="padding:4px 0 4px 14px;color:#555;font-size:13px;">• {name}</div>'
            html += '</div>'
    return html or '<div style="color:#999;font-style:italic;">No activities selected</div>'


def send_customer_confirmation(booking):
    """
    Send accurate HTML confirmation email to the customer.
    Uses exactly the data stored in the booking object.
    Structured to avoid spam filters.
    """
    activities = booking.get_activities_list()
    activities_html = _build_activities_html_for_customer(activities)

    # Readable display values
    travel_type_display = booking.get_travel_type_display() if booking.travel_type else 'Not specified'
    travelers_display = booking.get_travelers_display() if hasattr(booking, 'get_travelers_display') else booking.travelers
    accommodation_display = booking.get_accommodation_display() if booking.accommodation else 'Not specified'
    flexibility_display = booking.get_date_flexibility_display()
    start_date_str = booking.start_date.strftime('%B %d, %Y') if booking.start_date else 'Flexible'
    end_date_str = booking.end_date.strftime('%B %d, %Y') if booking.end_date else 'Flexible'
    submitted_str = booking.created_at.strftime('%B %d, %Y at %I:%M %p')
    booking_id = booking.get_booking_id()
    full_name = booking.get_full_name()

    special_requests_block = ''
    if booking.special_requests:
        special_requests_block = f"""
        <tr>
          <td style="padding:0 40px 28px;">
            <h2 style="margin:0 0 16px 0;color:#000;font-size:18px;font-weight:700;padding-bottom:8px;border-bottom:2px solid #f0f0f0;">Special Requests</h2>
            <div style="padding:18px;background:#fafafa;border-radius:8px;color:#555;font-size:14px;line-height:1.7;">
              {booking.special_requests}
            </div>
          </td>
        </tr>"""

    html_message = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width,initial-scale=1.0">
  <title>Booking Confirmation — Discover Rwanda</title>
</head>
<body style="margin:0;padding:0;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Arial,sans-serif;background:#f5f5f5;">
<table width="100%" cellpadding="0" cellspacing="0" border="0" style="background:#f5f5f5;padding:40px 20px;">
  <tr><td align="center">
    <table width="600" cellpadding="0" cellspacing="0" border="0"
           style="background:#fff;border-radius:12px;overflow:hidden;box-shadow:0 4px 20px rgba(0,0,0,0.08);max-width:600px;">

      <!-- HEADER -->
      <tr>
        <td style="background:#000;padding:44px 40px;text-align:center;">
          <div style="color:#fff;font-size:22px;font-weight:800;letter-spacing:4px;">DISCOVER RWANDA</div>
          <div style="color:rgba(255,255,255,0.65);font-size:12px;letter-spacing:2px;margin-top:6px;">LAND OF A THOUSAND HILLS</div>
        </td>
      </tr>

      <!-- STATUS BADGE -->
      <tr>
        <td style="padding:36px 40px 24px;text-align:center;">
          <div style="display:inline-block;background:#000;color:#fff;padding:10px 28px;border-radius:50px;font-size:12px;font-weight:700;letter-spacing:1.5px;margin-bottom:18px;">
            ✓ BOOKING RECEIVED
          </div>
          <h1 style="margin:0 0 12px 0;color:#000;font-size:28px;font-weight:700;line-height:1.2;">
            Dear {booking.first_name}, your journey begins!
          </h1>
          <p style="margin:0;color:#666;font-size:15px;line-height:1.6;">
            We've received your booking request and our travel specialists are already preparing your personalised itinerary.
          </p>
        </td>
      </tr>

      <!-- BOOKING REFERENCE -->
      <tr>
        <td style="padding:0 40px 28px;">
          <table width="100%" cellpadding="14" cellspacing="0" border="0"
                 style="background:#fafafa;border-radius:8px;border-left:4px solid #000;">
            <tr>
              <td>
                <div style="color:#999;font-size:11px;font-weight:700;letter-spacing:1px;text-transform:uppercase;margin-bottom:4px;">Booking Reference</div>
                <div style="color:#000;font-size:22px;font-weight:700;letter-spacing:1px;">{booking_id}</div>
                <div style="color:#666;font-size:12px;margin-top:4px;">Submitted on {submitted_str}</div>
              </td>
            </tr>
          </table>
        </td>
      </tr>

      <!-- PERSONAL INFORMATION -->
      <tr>
        <td style="padding:0 40px 28px;">
          <h2 style="margin:0 0 16px 0;color:#000;font-size:18px;font-weight:700;padding-bottom:8px;border-bottom:2px solid #f0f0f0;">Personal Information</h2>
          <table width="100%" cellpadding="0" cellspacing="0" border="0">
            <tr>
              <td style="padding:8px 0;width:50%;">
                <div style="color:#999;font-size:11px;font-weight:700;letter-spacing:1px;text-transform:uppercase;margin-bottom:4px;">Full Name</div>
                <div style="color:#333;font-size:15px;font-weight:600;">{full_name}</div>
              </td>
              <td style="padding:8px 0;">
                <div style="color:#999;font-size:11px;font-weight:700;letter-spacing:1px;text-transform:uppercase;margin-bottom:4px;">Number of Travellers</div>
                <div style="color:#333;font-size:15px;font-weight:600;">{travelers_display}</div>
              </td>
            </tr>
            <tr>
              <td style="padding:8px 0;">
                <div style="color:#999;font-size:11px;font-weight:700;letter-spacing:1px;text-transform:uppercase;margin-bottom:4px;">Email</div>
                <div style="color:#333;font-size:15px;">{booking.email}</div>
              </td>
              <td style="padding:8px 0;">
                <div style="color:#999;font-size:11px;font-weight:700;letter-spacing:1px;text-transform:uppercase;margin-bottom:4px;">Phone</div>
                <div style="color:#333;font-size:15px;">{booking.phone}</div>
              </td>
            </tr>
            <tr>
              <td style="padding:8px 0;" colspan="2">
                <div style="color:#999;font-size:11px;font-weight:700;letter-spacing:1px;text-transform:uppercase;margin-bottom:4px;">Country</div>
                <div style="color:#333;font-size:15px;">{booking.country}</div>
              </td>
            </tr>
          </table>
        </td>
      </tr>

      <!-- TRAVEL DETAILS -->
      <tr>
        <td style="padding:0 40px 28px;">
          <h2 style="margin:0 0 16px 0;color:#000;font-size:18px;font-weight:700;padding-bottom:8px;border-bottom:2px solid #f0f0f0;">Travel Details</h2>
          <table width="100%" cellpadding="0" cellspacing="0" border="0">
            <tr>
              <td style="padding:8px 0;width:50%;">
                <div style="color:#999;font-size:11px;font-weight:700;letter-spacing:1px;text-transform:uppercase;margin-bottom:4px;">Travel Style</div>
                <div style="color:#333;font-size:15px;font-weight:600;">{travel_type_display}</div>
              </td>
              <td style="padding:8px 0;">
                <div style="color:#999;font-size:11px;font-weight:700;letter-spacing:1px;text-transform:uppercase;margin-bottom:4px;">Duration</div>
                <div style="color:#333;font-size:15px;font-weight:600;">{booking.duration} days</div>
              </td>
            </tr>
            <tr>
              <td style="padding:8px 0;">
                <div style="color:#999;font-size:11px;font-weight:700;letter-spacing:1px;text-transform:uppercase;margin-bottom:4px;">Start Date</div>
                <div style="color:#333;font-size:15px;">{start_date_str}</div>
              </td>
              <td style="padding:8px 0;">
                <div style="color:#999;font-size:11px;font-weight:700;letter-spacing:1px;text-transform:uppercase;margin-bottom:4px;">End Date</div>
                <div style="color:#333;font-size:15px;">{end_date_str}</div>
              </td>
            </tr>
            <tr>
              <td style="padding:8px 0;">
                <div style="color:#999;font-size:11px;font-weight:700;letter-spacing:1px;text-transform:uppercase;margin-bottom:4px;">Date Flexibility</div>
                <div style="color:#333;font-size:15px;">{flexibility_display}</div>
              </td>
              <td style="padding:8px 0;">
                <div style="color:#999;font-size:11px;font-weight:700;letter-spacing:1px;text-transform:uppercase;margin-bottom:4px;">Budget per Person</div>
                <div style="color:#000;font-size:17px;font-weight:700;">{booking.get_budget_range_display()}</div>
              </td>
            </tr>
            <tr>
              <td style="padding:8px 0;" colspan="2">
                <div style="color:#999;font-size:11px;font-weight:700;letter-spacing:1px;text-transform:uppercase;margin-bottom:4px;">Accommodation</div>
                <div style="color:#333;font-size:15px;">{accommodation_display}</div>
              </td>
            </tr>
          </table>
        </td>
      </tr>

      <!-- ACTIVITIES -->
      <tr>
        <td style="padding:0 40px 28px;">
          <h2 style="margin:0 0 16px 0;color:#000;font-size:18px;font-weight:700;padding-bottom:8px;border-bottom:2px solid #f0f0f0;">Selected Activities &amp; Experiences</h2>
          {activities_html}
        </td>
      </tr>

      <!-- SPECIAL REQUESTS (conditional) -->
      {special_requests_block}

      <!-- NEXT STEPS -->
      <tr>
        <td style="padding:0 40px 28px;">
          <div style="background:#fafafa;padding:26px;border-radius:8px;border:2px solid #e8e8e8;">
            <h2 style="margin:0 0 16px 0;color:#000;font-size:18px;font-weight:700;">What Happens Next?</h2>
            <table width="100%" cellpadding="0" cellspacing="0" border="0">
              <tr><td style="padding:8px 0;">
                <div style="color:#000;font-size:14px;font-weight:600;">✓ Expert Review</div>
                <div style="color:#666;font-size:13px;margin-top:4px;">Our Rwanda travel specialists will carefully review your request</div>
              </td></tr>
              <tr><td style="padding:8px 0;">
                <div style="color:#000;font-size:14px;font-weight:600;">✓ Personalised Itinerary</div>
                <div style="color:#666;font-size:13px;margin-top:4px;">You'll receive a custom itinerary within 24 hours</div>
              </td></tr>
              <tr><td style="padding:8px 0;">
                <div style="color:#000;font-size:14px;font-weight:600;">✓ Complete Details</div>
                <div style="color:#666;font-size:13px;margin-top:4px;">Accommodation options, activities, and transparent pricing included</div>
              </td></tr>
              <tr><td style="padding:8px 0;">
                <div style="color:#000;font-size:14px;font-weight:600;">✓ Perfect Your Trip</div>
                <div style="color:#666;font-size:13px;margin-top:4px;">Modify the itinerary until it's exactly what you dreamed of</div>
              </td></tr>
            </table>
          </div>
        </td>
      </tr>

      <!-- CONTACT BLOCK -->
      <tr>
        <td style="padding:0 40px 28px;">
          <table width="100%" cellpadding="20" cellspacing="0" border="0" style="background:#000;border-radius:8px;">
            <tr>
              <td align="center">
                <h3 style="margin:0 0 16px 0;color:#fff;font-size:16px;font-weight:700;">Questions? We're Here to Help</h3>
                <table cellpadding="0" cellspacing="0" border="0" style="margin:0 auto;">
                  <tr>
                    <td style="padding:6px 18px;text-align:left;">
                      <div style="color:rgba(255,255,255,0.6);font-size:11px;margin-bottom:2px;">Email</div>
                      <a href="mailto:helpdiscoverrwanda@gmail.com" style="color:#fff;text-decoration:none;font-size:13px;font-weight:600;">helpdiscoverrwanda@gmail.com</a>
                    </td>
                    <td style="padding:6px 18px;text-align:left;">
                      <div style="color:rgba(255,255,255,0.6);font-size:11px;margin-bottom:2px;">Phone</div>
                      <a href="tel:+250798919909" style="color:#fff;text-decoration:none;font-size:13px;font-weight:600;">+250 798 919 909</a>
                    </td>
                  </tr>
                </table>
              </td>
            </tr>
          </table>
        </td>
      </tr>

      <!-- FOOTER -->
      <tr>
        <td style="padding:24px 40px;text-align:center;background:#fafafa;border-top:1px solid #e8e8e8;">
          <p style="margin:0 0 8px 0;color:#000;font-size:15px;font-weight:600;">Discover Rwanda</p>
          <p style="margin:0 0 12px 0;color:#666;font-size:12px;">Your gateway to extraordinary African adventures</p>
          <p style="margin:14px 0 0 0;color:#999;font-size:11px;">© 2026 Discover Rwanda. All rights reserved.</p>
        </td>
      </tr>

    </table>
  </td></tr>
</table>
</body>
</html>"""

    # Plain-text fallback (important for spam scoring)
    activities_text = '\n'.join(
        f"  • {ACTIVITY_LABELS.get(a, a.replace('-', ' ').title())}" for a in activities
    ) or '  • To be discussed during planning'

    text_message = f"""Dear {booking.first_name},

Thank you for choosing Discover Rwanda!
We have received your booking request and will contact you within 24 hours.

BOOKING REFERENCE: {booking_id}
Submitted: {submitted_str}

─────────────────────────────────────
PERSONAL INFORMATION
─────────────────────────────────────
Name:        {full_name}
Email:       {booking.email}
Phone:       {booking.phone}
Country:     {booking.country}
Travellers:  {travelers_display}

─────────────────────────────────────
TRAVEL DETAILS
─────────────────────────────────────
Travel Style:   {travel_type_display}
Start Date:     {start_date_str}
End Date:       {end_date_str}
Duration:       {booking.duration} days
Flexibility:    {flexibility_display}
Accommodation:  {accommodation_display}
Budget/Person:  {booking.get_budget_range_display()}

─────────────────────────────────────
SELECTED ACTIVITIES
─────────────────────────────────────
{activities_text}

{"─────────────────────────────────────" + chr(10) + "SPECIAL REQUESTS" + chr(10) + "─────────────────────────────────────" + chr(10) + booking.special_requests + chr(10) if booking.special_requests else ""}
─────────────────────────────────────
WHAT HAPPENS NEXT?
─────────────────────────────────────
✓ Our specialists will review your request
✓ Personalised itinerary delivered within 24 hours
✓ Includes accommodation, activities, and pricing
✓ Adjust freely until it's perfect

CONTACT US
Email:   helpdiscoverrwanda@gmail.com
Phone:   +250 798 919 909

Best regards,
The Discover Rwanda Team
— Land of a Thousand Hills
"""

    email_msg = EmailMultiAlternatives(
        subject=f'Booking Confirmed — {booking_id} | Discover Rwanda',
        body=text_message,
        from_email=f'Discover Rwanda <{settings.DEFAULT_FROM_EMAIL}>',
        to=[booking.email],
        reply_to=['helpdiscoverrwanda@gmail.com'],
        headers={
            'List-Unsubscribe': '<mailto:helpdiscoverrwanda@gmail.com?subject=unsubscribe>',
            'X-Mailer': 'DiscoverRwanda-Booking/1.0',
        }
    )
    email_msg.attach_alternative(html_message, "text/html")
    email_msg.send(fail_silently=False)
    print(f"✅ Confirmation email sent to {booking.email}")
    return True


def send_admin_notification(booking):
    """Send detailed booking notification to admin."""
    activities = booking.get_activities_list()
    activities_html = _build_activities_html_for_admin(activities)

    travel_type_display = booking.get_travel_type_display() if booking.travel_type else 'Not specified'
    travelers_display = booking.get_travelers_display() if hasattr(booking, 'get_travelers_display') else booking.travelers
    accommodation_display = booking.get_accommodation_display() if booking.accommodation else 'Not specified'
    flexibility_display = booking.get_date_flexibility_display()
    start_date_str = booking.start_date.strftime('%B %d, %Y') if booking.start_date else 'Flexible'
    end_date_str = booking.end_date.strftime('%B %d, %Y') if booking.end_date else 'Flexible'
    submitted_str = booking.created_at.strftime('%B %d, %Y at %I:%M %p')
    booking_id = booking.get_booking_id()
    full_name = booking.get_full_name()

    # Safe total budget calculation
    try:
        traveler_count = int(booking.travelers.split('-')[0].replace('+', ''))
    except Exception:
        traveler_count = 1
    total_budget = booking.budget * traveler_count

    html_message = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>New Booking — {booking_id}</title>
</head>
<body style="margin:0;padding:0;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Arial,sans-serif;background:#f5f5f5;">
<table width="100%" cellpadding="0" cellspacing="0" border="0" style="background:#f5f5f5;padding:40px 20px;">
  <tr><td align="center">
    <table width="650" cellpadding="0" cellspacing="0" border="0"
           style="background:#fff;border-radius:12px;overflow:hidden;box-shadow:0 4px 20px rgba(0,0,0,0.08);max-width:650px;">

      <!-- HEADER -->
      <tr>
        <td style="background:#000;padding:36px 40px;">
          <div style="color:#fff;font-size:20px;font-weight:700;margin-bottom:4px;">🔔 New Booking Request</div>
          <div style="color:rgba(255,255,255,0.6);font-size:12px;">{submitted_str}</div>
          <div style="margin-top:10px;display:inline-block;background:rgba(255,255,255,0.15);border:1px solid rgba(255,255,255,0.3);padding:6px 16px;border-radius:50px;color:#fff;font-size:12px;font-weight:700;letter-spacing:1px;">{booking_id}</div>
        </td>
      </tr>

      <!-- PRIORITY INFO -->
      <tr>
        <td style="padding:28px 40px;">
          <table width="100%" cellpadding="18" cellspacing="0" border="0"
                 style="background:#fafafa;border-radius:8px;border-left:4px solid #000;">
            <tr>
              <td style="width:50%;padding-right:14px;">
                <div style="color:#999;font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:1px;margin-bottom:6px;">Budget Range (per person)</div>
                <div style="color:#000;font-size:22px;font-weight:700;">{booking.get_budget_range_display()}</div>
                <div style="color:#666;font-size:12px;margin-top:2px;">× {travelers_display}</div>
              </td>
              <td style="width:50%;padding-left:14px;border-left:2px solid #e8e8e8;">
                <div style="color:#999;font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:1px;margin-bottom:6px;">Trip Duration</div>
                <div style="color:#000;font-size:26px;font-weight:700;">{booking.duration} Days</div>
                <div style="color:#666;font-size:12px;margin-top:2px;">{start_date_str} → {end_date_str}</div>
              </td>
            </tr>
          </table>
        </td>
      </tr>

      <!-- QUICK ACTIONS -->
      <tr>
        <td style="padding:0 40px 28px;">
          <div style="color:#999;font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:1px;margin-bottom:12px;">Quick Actions</div>
          <table width="100%" cellpadding="0" cellspacing="0" border="0">
            <tr>
              <td style="padding-right:8px;">
                <a href="mailto:{booking.email}" style="display:block;background:#000;color:#fff;text-align:center;padding:13px 16px;border-radius:8px;text-decoration:none;font-size:12px;font-weight:700;letter-spacing:0.5px;">✉ EMAIL CLIENT</a>
              </td>
              <td style="padding:0 8px;">
                <a href="tel:{booking.phone}" style="display:block;background:#000;color:#fff;text-align:center;padding:13px 16px;border-radius:8px;text-decoration:none;font-size:12px;font-weight:700;letter-spacing:0.5px;">📞 CALL CLIENT</a>
              </td>
              <td style="padding-left:8px;">
                <a href="/dashboard/booking/{booking.id}/" style="display:block;background:#fafafa;color:#000;text-align:center;padding:13px 16px;border-radius:8px;text-decoration:none;font-size:12px;font-weight:700;letter-spacing:0.5px;border:2px solid #e8e8e8;">⚙ VIEW IN DASHBOARD</a>
              </td>
            </tr>
          </table>
        </td>
      </tr>

      <!-- CUSTOMER INFO -->
      <tr>
        <td style="padding:0 40px 28px;">
          <h2 style="margin:0 0 14px 0;color:#000;font-size:16px;font-weight:700;padding-bottom:8px;border-bottom:2px solid #f0f0f0;">Customer Information</h2>
          <table width="100%" cellpadding="0" cellspacing="0" border="0" style="background:#fafafa;border-radius:8px;padding:18px;">
            <tr>
              <td style="padding:7px 0;width:50%;">
                <div style="color:#999;font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:1px;margin-bottom:4px;">Full Name</div>
                <div style="color:#000;font-size:14px;font-weight:600;">{full_name}</div>
              </td>
              <td style="padding:7px 0;">
                <div style="color:#999;font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:1px;margin-bottom:4px;">Travellers</div>
                <div style="color:#000;font-size:14px;font-weight:600;">{travelers_display}</div>
              </td>
            </tr>
            <tr>
              <td style="padding:7px 0;">
                <div style="color:#999;font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:1px;margin-bottom:4px;">Email</div>
                <a href="mailto:{booking.email}" style="color:#000;text-decoration:none;font-size:14px;">{booking.email}</a>
              </td>
              <td style="padding:7px 0;">
                <div style="color:#999;font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:1px;margin-bottom:4px;">Phone</div>
                <a href="tel:{booking.phone}" style="color:#000;text-decoration:none;font-size:14px;">{booking.phone}</a>
              </td>
            </tr>
            <tr>
              <td style="padding:7px 0;" colspan="2">
                <div style="color:#999;font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:1px;margin-bottom:4px;">Country</div>
                <div style="color:#000;font-size:14px;font-weight:600;">{booking.country}</div>
              </td>
            </tr>
          </table>
        </td>
      </tr>

      <!-- TRAVEL DETAILS -->
      <tr>
        <td style="padding:0 40px 28px;">
          <h2 style="margin:0 0 14px 0;color:#000;font-size:16px;font-weight:700;padding-bottom:8px;border-bottom:2px solid #f0f0f0;">Travel Details</h2>
          <table width="100%" cellpadding="0" cellspacing="0" border="0">
            <tr>
              <td style="padding:7px 0;width:50%;">
                <div style="color:#999;font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:1px;margin-bottom:4px;">Travel Style</div>
                <div style="color:#333;font-size:14px;">{travel_type_display}</div>
              </td>
              <td style="padding:7px 0;">
                <div style="color:#999;font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:1px;margin-bottom:4px;">Date Flexibility</div>
                <div style="color:#333;font-size:14px;">{flexibility_display}</div>
              </td>
            </tr>
            <tr>
              <td style="padding:7px 0;">
                <div style="color:#999;font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:1px;margin-bottom:4px;">Accommodation</div>
                <div style="color:#333;font-size:14px;">{accommodation_display}</div>
              </td>
              <td style="padding:7px 0;">
                <div style="color:#999;font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:1px;margin-bottom:4px;">Budget / Person</div>
                <div style="color:#000;font-size:15px;font-weight:700;">{booking.get_budget_range_display()}</div>
              </td>
            </tr>
          </table>
        </td>
      </tr>

      <!-- ACTIVITIES -->
      <tr>
        <td style="padding:0 40px 28px;">
          <h2 style="margin:0 0 14px 0;color:#000;font-size:16px;font-weight:700;padding-bottom:8px;border-bottom:2px solid #f0f0f0;">Selected Activities ({len(activities)} total)</h2>
          <div style="background:#fafafa;padding:18px;border-radius:8px;">{activities_html}</div>
        </td>
      </tr>

      <!-- SPECIAL REQUESTS -->
      <tr>
        <td style="padding:0 40px 28px;">
          <h2 style="margin:0 0 14px 0;color:#000;font-size:16px;font-weight:700;padding-bottom:8px;border-bottom:2px solid #f0f0f0;">Special Requests</h2>
          {"<div style='padding:16px;background:#fff8e1;border-left:4px solid #ffc107;border-radius:8px;color:#555;font-size:14px;line-height:1.7;'>" + booking.special_requests + "</div>" if booking.special_requests else "<div style='color:#999;font-style:italic;font-size:14px;'>None provided</div>"}
        </td>
      </tr>

      <!-- ACTION REMINDER -->
      <tr>
        <td style="padding:0 40px 36px;">
          <table width="100%" cellpadding="20" cellspacing="0" border="0" style="background:#000;border-radius:8px;">
            <tr>
              <td>
                <h3 style="margin:0 0 10px 0;color:#fff;font-size:15px;font-weight:700;">⏰ Action Required</h3>
                <p style="margin:0;color:rgba(255,255,255,0.85);font-size:13px;line-height:1.6;">
                  Client expects a personalised itinerary within 24 hours. Please review this booking and prepare a comprehensive proposal including accommodation options, detailed activities, and transparent pricing.
                </p>
              </td>
            </tr>
          </table>
        </td>
      </tr>

      <!-- FOOTER -->
      <tr>
        <td style="padding:20px 40px;text-align:center;background:#fafafa;border-top:1px solid #e8e8e8;">
          <p style="margin:0;color:#999;font-size:11px;">Automated notification · Discover Rwanda Booking System</p>
          <p style="margin:6px 0 0 0;color:#999;font-size:11px;">Booking: {booking_id} · Client: {booking.email}</p>
        </td>
      </tr>

    </table>
  </td></tr>
</table>
</body>
</html>"""

    activities_text = '\n'.join(
        f"  • {ACTIVITY_LABELS.get(a, a.replace('-', ' ').title())}" for a in activities
    ) or '  • None selected'

    text_message = f"""NEW BOOKING REQUEST — {booking_id}
Submitted: {submitted_str}

Budget Range:  {booking.get_budget_range_display()} × {travelers_display}  |  Duration: {booking.duration} days
Dates: {start_date_str} → {end_date_str}

CUSTOMER
  Name:       {full_name}
  Email:      {booking.email}
  Phone:      {booking.phone}
  Country:    {booking.country}
  Travellers: {travelers_display}

TRAVEL DETAILS
  Style:          {travel_type_display}
  Flexibility:    {flexibility_display}
  Accommodation:  {accommodation_display}
  Budget/Person:  {booking.get_budget_range_display()}

ACTIVITIES ({len(activities)} total)
{activities_text}

SPECIAL REQUESTS
{booking.special_requests or 'None provided'}

Dashboard: /dashboard/booking/{booking.id}/
Email client: {booking.email}
Call client: {booking.phone}

⏰ Client expects itinerary within 24 hours.
"""

    admin_email = getattr(settings, 'ADMIN_EMAIL', settings.DEFAULT_FROM_EMAIL)
    email_msg = EmailMultiAlternatives(
        subject=f'🔔 New Booking {booking_id} — {full_name}',
        body=text_message,
        from_email=f'Discover Rwanda Bookings <{settings.DEFAULT_FROM_EMAIL}>',
        to=[admin_email],
        reply_to=[booking.email],
    )
    email_msg.attach_alternative(html_message, "text/html")
    email_msg.send(fail_silently=False)
    print(f"✅ Admin notification sent to {admin_email}")
    return True


# ────────────────────────────────────────────────────────────
# ADMIN LOGIN / LOGOUT
# ────────────────────────────────────────────────────────────

def admin_login(request):
    """Custom login page for the admin dashboard."""
    if request.user.is_authenticated:
        return redirect('dashboard')

    error = None
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        user = authenticate(request, username=username, password=password)
        if user is not None and user.is_staff:
            login(request, user)
            next_url = request.POST.get('next') or request.GET.get('next') or 'dashboard'
            return redirect(next_url)
        else:
            error = 'Invalid credentials or insufficient permissions.'

    return render(request, 'adminpanel/login.html', {'error': error})


def admin_logout(request):
    logout(request)
    return redirect('admin_login')


# ────────────────────────────────────────────────────────────
# DASHBOARD VIEWS (all protected by login)
# ────────────────────────────────────────────────────────────

@login_required(login_url='admin_login')
def dashboard(request):
    bookings = TravelBooking.objects.all().order_by('-created_at')

    # ── Core stats ────────────────────────────────────────────
    total_bookings     = bookings.count()
    pending_requests   = bookings.filter(status='pending').count()
    confirmed_count    = bookings.filter(status='confirmed').count()
    processed_count    = bookings.filter(status='processed').count()
    processed_requests = confirmed_count + processed_count
    cancelled          = bookings.filter(status='cancelled').count()
    processed_rate     = round((processed_requests / total_bookings * 100), 1) if total_bookings else 0

    # ── Budget summary — use range midpoints for meaningful estimate ──
    BUDGET_MIDPOINTS = {
        range(500,  1000):  750,
        range(1000, 3000):  2000,
        range(3000, 6000):  4500,
        range(6000, 10000): 8000,
    }
    def budget_midpoint(b):
        for r, mid in BUDGET_MIDPOINTS.items():
            if b in r:
                return mid
        return 15000  # 10000+

    def traveler_count_from_str(t):
        try:
            return int(str(t).split('-')[0].replace('+','').strip())
        except Exception:
            return 1

    total_revenue = sum(
        budget_midpoint(b.budget) * traveler_count_from_str(b.travelers)
        for b in bookings if b.budget
    )

    # ── Month-over-month booking count change ─────────────────
    today = date.today()
    this_month_start  = today.replace(day=1)
    last_month_end    = this_month_start - timedelta(days=1)
    last_month_start  = last_month_end.replace(day=1)
    this_month_count  = bookings.filter(created_at__date__gte=this_month_start).count()
    last_month_count  = bookings.filter(
        created_at__date__gte=last_month_start,
        created_at__date__lte=last_month_end
    ).count()
    if last_month_count > 0:
        total_change = round(((this_month_count - last_month_count) / last_month_count * 100), 1)
        change_label = f"{'+' if total_change >= 0 else ''}{total_change}% vs last month"
        change_positive = total_change >= 0
    else:
        total_change = 0
        change_label = f"{this_month_count} booking{'s' if this_month_count != 1 else ''} this month"
        change_positive = True

    # ── Chart data: bookings per day, last 30 days ───────────
    thirty_days_ago = today - timedelta(days=29)
    chart_labels, chart_data = [], []
    for i in range(30):
        d = thirty_days_ago + timedelta(days=i)
        chart_labels.append(d.strftime('%b %d'))
        chart_data.append(bookings.filter(created_at__date=d).count())

    # ── Travel type breakdown ─────────────────────────────────
    travel_counts = {}
    for b in bookings:
        key = b.get_travel_type_display() if b.travel_type else 'Other'
        travel_counts[key] = travel_counts.get(key, 0) + 1

    # ── Filters (search + status, preserve both in query) ────
    status_filter = request.GET.get('status', '').strip()
    search_q      = request.GET.get('q', '').strip()
    filtered_bookings = bookings
    if status_filter:
        filtered_bookings = filtered_bookings.filter(status=status_filter)
    if search_q:
        filtered_bookings = filtered_bookings.filter(
            Q(first_name__icontains=search_q) |
            Q(last_name__icontains=search_q)  |
            Q(email__icontains=search_q)       |
            Q(country__icontains=search_q)
        )

    # Format revenue
    if total_revenue >= 1_000_000:
        revenue_display = f'${total_revenue/1_000_000:.1f}M'
    elif total_revenue >= 1_000:
        revenue_display = f'${total_revenue:,}'
    else:
        revenue_display = f'${total_revenue}'

    context = {
        'bookings': filtered_bookings,
        'total_bookings': total_bookings,
        'pending_requests': pending_requests,
        'processed_requests': processed_requests,
        'cancelled': cancelled,
        'processed_rate': processed_rate,
        'revenue': revenue_display,
        'change_label': change_label,
        'change_positive': change_positive,
        'total_change': total_change,
        'notifications_count': pending_requests,
        'chart_labels': json.dumps(chart_labels),
        'chart_data': json.dumps(chart_data),
        'travel_type_labels': json.dumps(list(travel_counts.keys())),
        'travel_type_data': json.dumps(list(travel_counts.values())),
        'status_filter': status_filter,
        'search_q': search_q,
    }
    return render(request, 'adminpanel/dashboard.html', context)


@login_required(login_url='admin_login')
def booking_view(request, pk):
    booking = get_object_or_404(TravelBooking, pk=pk)
    # Use midpoint of budget range for per-day calc
    BUDGET_MIDPOINTS = [
        (500,  1000,  750),
        (1000, 3000,  2000),
        (3000, 6000,  4500),
        (6000, 10000, 8000),
    ]
    budget_mid = 15000
    for lo, hi, mid in BUDGET_MIDPOINTS:
        if lo <= booking.budget < hi:
            budget_mid = mid
            break
    per_day = round(budget_mid / booking.duration, 2) if booking.duration else budget_mid

    pending_count = TravelBooking.objects.filter(status='pending').count()
    context = {
        'booking': booking,
        'budget_range': booking.get_budget_range_display(),
        'per_day': per_day,
        'pending_count': pending_count,
        'activities': [
            ACTIVITY_LABELS.get(a, a.replace('-', ' ').title())
            for a in booking.get_activities_list()
        ],
    }
    return render(request, 'adminpanel/booking_view.html', context)


@login_required(login_url='admin_login')
def booking_edit(request, pk):
    booking = get_object_or_404(TravelBooking, pk=pk)
    if request.method == 'POST':
        form = TravelBookingForm(request.POST, instance=booking)
        if form.is_valid():
            form.save()
            messages.success(request, f'Booking {booking.get_booking_id()} updated successfully.')
            return redirect('booking_view', pk=pk)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = TravelBookingForm(instance=booking)
    return render(request, 'adminpanel/booking_edit.html', {'form': form, 'booking': booking})


@login_required(login_url='admin_login')
def booking_delete(request, pk):
    booking = get_object_or_404(TravelBooking, pk=pk)
    if request.method == 'POST':
        booking_id = booking.get_booking_id()
        booking.delete()
        messages.success(request, f'Booking {booking_id} has been deleted.')
        return redirect('dashboard')
    return render(request, 'adminpanel/booking_confirm_delete.html', {'booking': booking})


@login_required(login_url='admin_login')
def booking_pdf(request, pk):
    booking = get_object_or_404(TravelBooking, pk=pk)
    template = get_template("adminpanel/booking_pdf.html")
    html = template.render({
        "booking": booking,
        "activities": [
            ACTIVITY_LABELS.get(a, a.replace('-', ' ').title())
            for a in booking.get_activities_list()
        ],
    })
    result = io.BytesIO()
    pdf = pisa.CreatePDF(io.StringIO(html), dest=result)
    if pdf.err:
        return HttpResponse("PDF generation error", status=500)
    response = HttpResponse(result.getvalue(), content_type="application/pdf")
    response["Content-Disposition"] = f'inline; filename="booking_{booking.pk}.pdf"'
    return response


@login_required(login_url='admin_login')
@require_POST
def booking_mark_processed(request, pk):
    booking = get_object_or_404(TravelBooking, pk=pk)
    booking.mark_as_processed()
    messages.success(request, f'Booking {booking.get_booking_id()} marked as Processed.')
    return redirect('booking_view', pk=pk)


@login_required(login_url='admin_login')
@require_POST
def booking_mark_confirmed(request, pk):
    booking = get_object_or_404(TravelBooking, pk=pk)
    booking.mark_as_confirmed()
    messages.success(request, f'Booking {booking.get_booking_id()} marked as Confirmed.')
    return redirect('booking_view', pk=pk)


@login_required(login_url='admin_login')
@require_POST
def booking_cancel(request, pk):
    booking = get_object_or_404(TravelBooking, pk=pk)
    booking.cancel_booking()
    messages.success(request, f'Booking {booking.get_booking_id()} has been cancelled.')
    return redirect('booking_view', pk=pk)
