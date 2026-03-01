from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.mail import send_mail, EmailMessage
from django.template.loader import render_to_string
from django.conf import settings
from django.template.loader import get_template
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.utils.html import strip_tags
from django.views.generic import ListView, DetailView
from .models import TravelBooking
from .forms import TravelBookingForm
from django.http import HttpResponse
from xhtml2pdf import pisa  # You can install it with `pip install xhtml2pdf`
from io import BytesIO
import io

# Create your views here.
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

# def success(request):
#     return render(request, "success.html")




def contact_form_view(request):
    """
    Main contact/booking form view
    Handles both GET (display form) and POST (process submission)
    """
    if request.method == 'POST':
        form = TravelBookingForm(request.POST)
        print (request.body)
        
        if form.is_valid():
            # Save booking to database
            booking = form.save(commit=False)
            
            # Capture additional metadata (if needed)
            try:
                booking.ip_address = get_client_ip(request)
                booking.user_agent = request.META.get('HTTP_USER_AGENT', '')[:500]
            except:
                pass
            
            booking.save()
            
            # Send confirmation email to customer
            try:
                send_customer_confirmation(booking)
            except Exception as e:
                print(f"Error sending customer email: {e}")
            
            # Send notification email to admin
            try:
                send_admin_notification(booking)
            except Exception as e:
                print(f"Error sending admin email: {e}")
            
            # Success message
            messages.success(
                request,
                f'Thank you {booking.first_name}! Your booking request has been received. '
                'We\'ll get back to you within 24 hours with a personalized itinerary.'
            )
            
            # Redirect to success page
            return redirect('success')
        else:
            # Form has errors
            messages.error(
                request,
                'There were some errors in your submission. Please check the form and try again.'
            )
    else:
        # GET request - display empty form
        form = TravelBookingForm()
    
    context = {
        'form': form,
    }
    return render(request, 'contact.html', context)


@require_http_methods(["POST"])
def contact_form_ajax(request):
    """
    AJAX endpoint for async form submission
    Returns JSON response
    """
    form = TravelBookingForm(request.POST)
    
    if form.is_valid():
        # Save booking
        booking = form.save(commit=True)
        try:
            booking.ip_address = get_client_ip(request)
            booking.user_agent = request.META.get('HTTP_USER_AGENT', '')[:500]
        except:
            pass
        booking.save()
        
        # Send emails
        try:
            send_customer_confirmation(booking)
        except:
            pass
        
        try:
            send_admin_notification(booking)
        except:
            pass
        
        return JsonResponse({
            'success': True,
            'message': f'Thank you {booking.first_name}! Your booking request has been received.',
            'booking_id': booking.get_booking_id(),
            'redirect_url': 'success'
        })
    else:
        return JsonResponse({
            'success': False,
            'message': 'Please correct the errors in the form.',
            'errors': form.errors
        }, status=400)


def success(request):
    """Success page after form submission"""
    return render(request, 'success.html')


def get_client_ip(request):
    """Extract client IP address from request"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def send_customer_confirmation(booking):
    """
    Send premium HTML confirmation email to customer
    Returns True if successful, False otherwise
    """
    try:
        subject = f'Your Rwanda Journey Begins - Booking #{booking.get_booking_id()}'
        
        # Organize activities by category
        activities = booking.get_activities_list() if booking.get_activities_list() else []
        
        # Activity categories mapping
        wildlife_activities = ['gorilla-trekking', 'golden-monkey', 'chimpanzee']
        safari_activities = ['big-five', 'boat-safari', 'bird-watching']
        nature_activities = ['canopy-walk', 'guided-walks', 'waterfall-hikes', 'volcano-hiking', 'mountain-climbing']
        lake_activities = ['kayaking', 'congo-nile', 'sport-fishing', 'zip-lining', 'sunset-cruise', 'swimming-beach', 'spa-wellness', 'yoga-meditation', 'hot-springs', 'golf']
        cultural_activities = ['genocide-memorial', 'cultural-villages', 'traditional-dance', 'cooking-classes', 'art-workshops', 'museums-galleries', 'coffee-tours', 'tea-plantations', 'market-tours']
        city_activities = ['kigali-tour', 'fine-dining', 'street-food', 'nightlife-music', 'photography-tours', 'shopping']
        
        # Categorize selected activities
        categorized_activities = {
            '🦍 Wildlife & Primates': [act for act in activities if act in wildlife_activities],
            '🦁 Safari Experiences': [act for act in activities if act in safari_activities],
            '🌿 Nature & Adventure': [act for act in activities if act in nature_activities],
            '🏖️ Lake Kivu Activities': [act for act in activities if act in lake_activities],
            '🎭 Cultural Experiences': [act for act in activities if act in cultural_activities],
            '🏙️ Kigali City': [act for act in activities if act in city_activities],
        }
        
        # Build activities HTML
        activities_html = ''
        for category, acts in categorized_activities.items():
            if acts:
                activities_html += f'<div style="margin-bottom: 20px;"><h4 style="margin: 0 0 10px 0; color: #000; font-size: 15px; font-weight: 600;">{category}</h4>'
                for act in acts:
                    activity_name = act.replace('-', ' ').title()
                    activities_html += f'<div style="padding: 8px 0; color: #555; font-size: 14px;">• {activity_name}</div>'
                activities_html += '</div>'
        
        if not activities_html:
            activities_html = '<div style="color: #666; font-style: italic;">To be discussed during planning</div>'
        
        # Premium HTML email template
        html_message = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Rwanda Travel Booking Confirmation</title>
</head>
<body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; background-color: #f5f5f5;">
    
    <!-- Main Container -->
    <table width="100%" cellpadding="0" cellspacing="0" border="0" style="background-color: #f5f5f5; padding: 40px 20px;">
        <tr>
            <td align="center">
                
                <!-- Email Content -->
                <table width="600" cellpadding="0" cellspacing="0" border="0" style="background-color: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);">
                    
                    <!-- Header -->
                    <tr>
                        <td style="background: linear-gradient(135deg, #000000 0%, #1a1a1a 100%); padding: 50px 40px; text-align: center;">
                            <div style="color: #ffffff; font-size: 28px; font-weight: 700; letter-spacing: 2px; margin-bottom: 10px;">
                                🌿 DISCOVER RWANDA
                            </div>
                            <div style="color: rgba(255, 255, 255, 0.8); font-size: 14px; letter-spacing: 1px;">
                                LAND OF A THOUSAND HILLS
                            </div>
                        </td>
                    </tr>
                    
                    <!-- Success Badge -->
                    <tr>
                        <td style="padding: 40px 40px 30px; text-align: center;">
                            <div style="display: inline-block; background-color: #000; color: #fff; padding: 12px 30px; border-radius: 50px; font-size: 13px; font-weight: 700; letter-spacing: 1.5px; margin-bottom: 20px;">
                                ✓ BOOKING RECEIVED
                            </div>
                            <h1 style="margin: 0 0 15px 0; color: #000; font-size: 32px; font-weight: 700; line-height: 1.2;">
                                Your Journey Begins
                            </h1>
                            <p style="margin: 0; color: #666; font-size: 16px; line-height: 1.6;">
                                Thank you for choosing Discover Rwanda. We've received your booking request and our travel specialists are preparing your personalized itinerary.
                            </p>
                        </td>
                    </tr>
                    
                    <!-- Booking ID -->
                    <tr>
                        <td style="padding: 0 40px 30px;">
                            <table width="100%" cellpadding="15" cellspacing="0" border="0" style="background-color: #fafafa; border-radius: 8px; border-left: 4px solid #000;">
                                <tr>
                                    <td>
                                        <div style="color: #999; font-size: 11px; font-weight: 700; letter-spacing: 1px; text-transform: uppercase; margin-bottom: 5px;">
                                            Booking Reference
                                        </div>
                                        <div style="color: #000; font-size: 24px; font-weight: 700; letter-spacing: 1px;">
                                            #{booking.get_booking_id()}
                                        </div>
                                        <div style="color: #666; font-size: 13px; margin-top: 5px;">
                                            Submitted on {booking.created_at.strftime('%B %d, %Y at %I:%M %p')}
                                        </div>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                    
                    <!-- Personal Information -->
                    <tr>
                        <td style="padding: 0 40px 30px;">
                            <h2 style="margin: 0 0 20px 0; color: #000; font-size: 20px; font-weight: 700; padding-bottom: 10px; border-bottom: 2px solid #f0f0f0;">
                                Personal Information
                            </h2>
                            <table width="100%" cellpadding="0" cellspacing="0" border="0">
                                <tr>
                                    <td style="padding: 10px 0;">
                                        <div style="color: #999; font-size: 11px; font-weight: 700; letter-spacing: 1px; text-transform: uppercase; margin-bottom: 5px;">Name</div>
                                        <div style="color: #333; font-size: 15px; font-weight: 600;">{booking.get_full_name()}</div>
                                    </td>
                                    <td style="padding: 10px 0;">
                                        <div style="color: #999; font-size: 11px; font-weight: 700; letter-spacing: 1px; text-transform: uppercase; margin-bottom: 5px;">Travelers</div>
                                        <div style="color: #333; font-size: 15px; font-weight: 600;">{booking.get_travelers_display()}</div>
                                    </td>
                                </tr>
                                <tr>
                                    <td style="padding: 10px 0;">
                                        <div style="color: #999; font-size: 11px; font-weight: 700; letter-spacing: 1px; text-transform: uppercase; margin-bottom: 5px;">Email</div>
                                        <div style="color: #333; font-size: 15px;">{booking.email}</div>
                                    </td>
                                    <td style="padding: 10px 0;">
                                        <div style="color: #999; font-size: 11px; font-weight: 700; letter-spacing: 1px; text-transform: uppercase; margin-bottom: 5px;">Phone</div>
                                        <div style="color: #333; font-size: 15px;">{booking.phone}</div>
                                    </td>
                                </tr>
                                <tr>
                                    <td style="padding: 10px 0;" colspan="2">
                                        <div style="color: #999; font-size: 11px; font-weight: 700; letter-spacing: 1px; text-transform: uppercase; margin-bottom: 5px;">Country</div>
                                        <div style="color: #333; font-size: 15px;">{booking.country}</div>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                    
                    <!-- Travel Details -->
                    <tr>
                        <td style="padding: 0 40px 30px;">
                            <h2 style="margin: 0 0 20px 0; color: #000; font-size: 20px; font-weight: 700; padding-bottom: 10px; border-bottom: 2px solid #f0f0f0;">
                                Travel Details
                            </h2>
                            <table width="100%" cellpadding="0" cellspacing="0" border="0">
                                <tr>
                                    <td style="padding: 10px 0;">
                                        <div style="color: #999; font-size: 11px; font-weight: 700; letter-spacing: 1px; text-transform: uppercase; margin-bottom: 5px;">Travel Style</div>
                                        <div style="color: #333; font-size: 15px; font-weight: 600;">{booking.get_travel_type_display() if booking.travel_type else 'Not specified'}</div>
                                    </td>
                                    <td style="padding: 10px 0;">
                                        <div style="color: #999; font-size: 11px; font-weight: 700; letter-spacing: 1px; text-transform: uppercase; margin-bottom: 5px;">Duration</div>
                                        <div style="color: #333; font-size: 15px; font-weight: 600;">{booking.duration} days</div>
                                    </td>
                                </tr>
                                <tr>
                                    <td style="padding: 10px 0;">
                                        <div style="color: #999; font-size: 11px; font-weight: 700; letter-spacing: 1px; text-transform: uppercase; margin-bottom: 5px;">Start Date</div>
                                        <div style="color: #333; font-size: 15px;">{booking.start_date.strftime('%B %d, %Y') if booking.start_date else 'Flexible'}</div>
                                    </td>
                                    <td style="padding: 10px 0;">
                                        <div style="color: #999; font-size: 11px; font-weight: 700; letter-spacing: 1px; text-transform: uppercase; margin-bottom: 5px;">End Date</div>
                                        <div style="color: #333; font-size: 15px;">{booking.end_date.strftime('%B %d, %Y') if booking.end_date else 'Flexible'}</div>
                                    </td>
                                </tr>
                                <tr>
                                    <td style="padding: 10px 0;">
                                        <div style="color: #999; font-size: 11px; font-weight: 700; letter-spacing: 1px; text-transform: uppercase; margin-bottom: 5px;">Date Flexibility</div>
                                        <div style="color: #333; font-size: 15px;">{booking.get_date_flexibility_display()}</div>
                                    </td>
                                    <td style="padding: 10px 0;">
                                        <div style="color: #999; font-size: 11px; font-weight: 700; letter-spacing: 1px; text-transform: uppercase; margin-bottom: 5px;">Budget per Person</div>
                                        <div style="color: #000; font-size: 18px; font-weight: 700;">${booking.budget:,} USD</div>
                                    </td>
                                </tr>
                                <tr>
                                    <td style="padding: 10px 0;" colspan="2">
                                        <div style="color: #999; font-size: 11px; font-weight: 700; letter-spacing: 1px; text-transform: uppercase; margin-bottom: 5px;">Accommodation</div>
                                        <div style="color: #333; font-size: 15px;">{booking.get_accommodation_display() if booking.accommodation else 'Not specified'}</div>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                    
                    <!-- Selected Activities -->
                    <tr>
                        <td style="padding: 0 40px 30px;">
                            <h2 style="margin: 0 0 20px 0; color: #000; font-size: 20px; font-weight: 700; padding-bottom: 10px; border-bottom: 2px solid #f0f0f0;">
                                Selected Activities & Experiences
                            </h2>
                            {activities_html}
                        </td>
                    </tr>
                    
                    <!-- Special Requests -->
                    {f'''<tr>
                        <td style="padding: 0 40px 30px;">
                            <h2 style="margin: 0 0 20px 0; color: #000; font-size: 20px; font-weight: 700; padding-bottom: 10px; border-bottom: 2px solid #f0f0f0;">
                                Special Requests
                            </h2>
                            <div style="padding: 20px; background-color: #fafafa; border-radius: 8px; color: #555; font-size: 14px; line-height: 1.7;">
                                {booking.special_requests}
                            </div>
                        </td>
                    </tr>''' if booking.special_requests else ''}
                    
                    <!-- Next Steps -->
                    <tr>
                        <td style="padding: 0 40px 40px;">
                            <div style="background: linear-gradient(135deg, #fafafa 0%, #f5f5f5 100%); padding: 30px; border-radius: 8px; border: 2px solid #e8e8e8;">
                                <h2 style="margin: 0 0 20px 0; color: #000; font-size: 20px; font-weight: 700;">
                                    What Happens Next?
                                </h2>
                                <table width="100%" cellpadding="0" cellspacing="0" border="0">
                                    <tr>
                                        <td style="padding: 10px 0;">
                                            <div style="color: #000; font-size: 15px; font-weight: 600;">✓ Expert Review</div>
                                            <div style="color: #666; font-size: 14px; margin-top: 5px;">Our Rwanda travel specialists will carefully review your request</div>
                                        </td>
                                    </tr>
                                    <tr>
                                        <td style="padding: 10px 0;">
                                            <div style="color: #000; font-size: 15px; font-weight: 600;">✓ Personalized Itinerary</div>
                                            <div style="color: #666; font-size: 14px; margin-top: 5px;">You'll receive a custom itinerary within 24 hours</div>
                                        </td>
                                    </tr>
                                    <tr>
                                        <td style="padding: 10px 0;">
                                            <div style="color: #000; font-size: 15px; font-weight: 600;">✓ Complete Details</div>
                                            <div style="color: #666; font-size: 14px; margin-top: 5px;">We'll include accommodation options, activities, and transparent pricing</div>
                                        </td>
                                    </tr>
                                    <tr>
                                        <td style="padding: 10px 0;">
                                            <div style="color: #000; font-size: 15px; font-weight: 600;">✓ Perfect Your Trip</div>
                                            <div style="color: #666; font-size: 14px; margin-top: 5px;">Modify the itinerary until it's exactly what you dreamed of</div>
                                        </td>
                                    </tr>
                                </table>
                            </div>
                        </td>
                    </tr>
                    
                    <!-- Contact Information -->
                    <tr>
                        <td style="padding: 0 40px 40px;">
                            <table width="100%" cellpadding="20" cellspacing="0" border="0" style="background-color: #000; border-radius: 8px;">
                                <tr>
                                    <td align="center">
                                        <h3 style="margin: 0 0 20px 0; color: #fff; font-size: 18px; font-weight: 700;">
                                            Questions? We're Here to Help
                                        </h3>
                                        <table cellpadding="0" cellspacing="0" border="0" style="margin: 0 auto;">
                                            <tr>
                                                <td style="padding: 8px 20px; text-align: left;">
                                                    <div style="color: rgba(255, 255, 255, 0.7); font-size: 12px; margin-bottom: 3px;">Email</div>
                                                    <a href="mailto:info@discoverrwanda.com" style="color: #fff; text-decoration: none; font-size: 14px; font-weight: 600;">info@discoverrwanda.com</a>
                                                </td>
                                                <td style="padding: 8px 20px; text-align: left;">
                                                    <div style="color: rgba(255, 255, 255, 0.7); font-size: 12px; margin-bottom: 3px;">Phone</div>
                                                    <a href="tel:+250788123456" style="color: #fff; text-decoration: none; font-size: 14px; font-weight: 600;">+250 788 123 456</a>
                                                </td>
                                            </tr>
                                        </table>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                    
                    <!-- Footer -->
                    <tr>
                        <td style="padding: 30px 40px; text-align: center; background-color: #fafafa; border-top: 1px solid #e8e8e8;">
                            <p style="margin: 0 0 10px 0; color: #000; font-size: 16px; font-weight: 600;">
                                Discover Rwanda
                            </p>
                            <p style="margin: 0 0 15px 0; color: #666; font-size: 13px;">
                                Your gateway to extraordinary African adventures
                            </p>
                            <div style="margin: 20px 0;">
                                <a href="https://www.discoverrwanda.com" style="color: #000; text-decoration: none; margin: 0 10px; font-size: 13px; font-weight: 600;">Website</a>
                                <span style="color: #ccc;">|</span>
                                <a href="https://www.facebook.com/discoverrwanda" style="color: #000; text-decoration: none; margin: 0 10px; font-size: 13px; font-weight: 600;">Facebook</a>
                                <span style="color: #ccc;">|</span>
                                <a href="https://www.instagram.com/discoverrwanda" style="color: #000; text-decoration: none; margin: 0 10px; font-size: 13px; font-weight: 600;">Instagram</a>
                            </div>
                            <p style="margin: 15px 0 0 0; color: #999; font-size: 12px;">
                                © 2026 Discover Rwanda. All rights reserved.
                            </p>
                        </td>
                    </tr>
                    
                </table>
                
            </td>
        </tr>
    </table>
    
</body>
</html>
"""
        
        # Plain text version as fallback
        text_message = f"""
Dear {booking.first_name},

Thank you for your interest in visiting Rwanda!

BOOKING REFERENCE: #{booking.get_booking_id()}
Submitted: {booking.created_at.strftime('%B %d, %Y at %I:%M %p')}

PERSONAL INFORMATION
• Name: {booking.get_full_name()}
• Email: {booking.email}
• Phone: {booking.phone}
• Country: {booking.country}
• Travelers: {booking.get_travelers_display()}

TRAVEL DETAILS
• Travel Style: {booking.get_travel_type_display() if booking.travel_type else 'Not specified'}
• Start Date: {booking.start_date.strftime('%B %d, %Y') if booking.start_date else 'Flexible'}
• End Date: {booking.end_date.strftime('%B %d, %Y') if booking.end_date else 'Flexible'}
• Duration: {booking.duration} days
• Date Flexibility: {booking.get_date_flexibility_display()}
• Accommodation: {booking.get_accommodation_display() if booking.accommodation else 'Not specified'}
• Budget: ${booking.budget:,} USD per person

SELECTED ACTIVITIES
{chr(10).join('• ' + activity.replace('-', ' ').title() for activity in booking.get_activities_list()) if booking.get_activities_list() else '• To be discussed during planning'}

{f'SPECIAL REQUESTS{chr(10)}{booking.special_requests}{chr(10)}' if booking.special_requests else ''}
WHAT HAPPENS NEXT?
✓ Our Rwanda travel specialists will review your request
✓ You'll receive a personalized itinerary within 24 hours
✓ We'll include accommodation options, activities, and pricing
✓ Feel free to modify the itinerary until it's perfect for you

CONTACT US
Email: info@discoverrwanda.com
Phone: +250 787 931 403
Website: www.discoverrwanda.com

Best regards,
The Discover Rwanda Team

---
Discover Rwanda - Land of a Thousand Hills
Your gateway to extraordinary African adventures
"""
        
        # Send email with HTML
        from django.core.mail import EmailMultiAlternatives
        
        email = EmailMultiAlternatives(
            subject=subject,
            body=text_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[booking.email],
            reply_to=['info@discoverrwanda.com'],
        )
        email.attach_alternative(html_message, "text/html")
        email.send(fail_silently=False)
        
        print(f"✅ Premium confirmation email sent to {booking.email}")
        return True
        
    except Exception as e:
        print(f"❌ Error sending customer email: {e}")
        import traceback
        traceback.print_exc()
        return False



def send_admin_notification(booking):
    """
    Send premium HTML notification email to admin about new booking
    Returns True if successful, False otherwise
    """
    try:
        subject = f'🔔 New Booking #{booking.get_booking_id()} - {booking.get_full_name()}'
        
        # Organize activities by category
        activities = booking.get_activities_list() if booking.get_activities_list() else []
        
        # Activity categories mapping
        wildlife_activities = ['gorilla-trekking', 'golden-monkey', 'chimpanzee']
        safari_activities = ['big-five', 'boat-safari', 'bird-watching']
        nature_activities = ['canopy-walk', 'guided-walks', 'waterfall-hikes', 'volcano-hiking', 'mountain-climbing']
        lake_activities = ['kayaking', 'congo-nile', 'sport-fishing', 'zip-lining', 'sunset-cruise', 'swimming-beach', 'spa-wellness', 'yoga-meditation', 'hot-springs', 'golf']
        cultural_activities = ['genocide-memorial', 'cultural-villages', 'traditional-dance', 'cooking-classes', 'art-workshops', 'museums-galleries', 'coffee-tours', 'tea-plantations', 'market-tours']
        city_activities = ['kigali-tour', 'fine-dining', 'street-food', 'nightlife-music', 'photography-tours', 'shopping']
        
        # Categorize selected activities
        categorized_activities = {
            '🦍 Wildlife & Primates': [act for act in activities if act in wildlife_activities],
            '🦁 Safari Experiences': [act for act in activities if act in safari_activities],
            '🌿 Nature & Adventure': [act for act in activities if act in nature_activities],
            '🏖️ Lake Kivu Activities': [act for act in activities if act in lake_activities],
            '🎭 Cultural Experiences': [act for act in activities if act in cultural_activities],
            '🏙️ Kigali City': [act for act in activities if act in city_activities],
        }
        
        # Build activities HTML
        activities_html = ''
        for category, acts in categorized_activities.items():
            if acts:
                activities_html += f'<div style="margin-bottom: 15px;"><strong style="color: #000; font-size: 14px;">{category}</strong>'
                for act in acts:
                    activity_name = act.replace('-', ' ').title()
                    activities_html += f'<div style="padding: 5px 0 5px 15px; color: #555; font-size: 13px;">• {activity_name}</div>'
                activities_html += '</div>'
        
        if not activities_html:
            activities_html = '<div style="color: #999; font-style: italic;">No activities selected</div>'
        
        # Calculate total budget
        total_budget = booking.budget * int(booking.travelers.split()[0]) if booking.travelers and booking.budget else 0
        
        # Premium HTML admin email template
        html_message = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>New Booking Notification</title>
</head>
<body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; background-color: #f5f5f5;">
    
    <!-- Main Container -->
    <table width="100%" cellpadding="0" cellspacing="0" border="0" style="background-color: #f5f5f5; padding: 40px 20px;">
        <tr>
            <td align="center">
                
                <!-- Email Content -->
                <table width="650" cellpadding="0" cellspacing="0" border="0" style="background-color: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);">
                    
                    <!-- Header -->
                    <tr>
                        <td style="background: linear-gradient(135deg, #000000 0%, #1a1a1a 100%); padding: 40px; text-align: left;">
                            <table width="100%" cellpadding="0" cellspacing="0" border="0">
                                <tr>
                                    <td>
                                        <div style="color: #ffffff; font-size: 24px; font-weight: 700; margin-bottom: 5px;">
                                            🔔 New Booking Request
                                        </div>
                                        <div style="color: rgba(255, 255, 255, 0.7); font-size: 13px;">
                                            {booking.created_at.strftime('%B %d, %Y at %I:%M %p')}
                                        </div>
                                    </td>
                                    <td align="right">
                                        <div style="display: inline-block; background-color: rgba(255, 255, 255, 0.15); border: 1px solid rgba(255, 255, 255, 0.3); padding: 8px 20px; border-radius: 50px; color: #fff; font-size: 13px; font-weight: 700; letter-spacing: 1px;">
                                            #{booking.get_booking_id()}
                                        </div>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                    
                    <!-- Priority Info -->
                    <tr>
                        <td style="padding: 30px 40px;">
                            <table width="100%" cellpadding="0" cellspacing="0" border="0">
                                <tr>
                                    <td style="padding: 20px; background: linear-gradient(135deg, #fafafa 0%, #f5f5f5 100%); border-radius: 8px; border-left: 4px solid #000;">
                                        <table width="100%" cellpadding="0" cellspacing="0" border="0">
                                            <tr>
                                                <td style="width: 50%; padding-right: 15px;">
                                                    <div style="color: #999; font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 8px;">Total Trip Value</div>
                                                    <div style="color: #000; font-size: 28px; font-weight: 700;">${total_budget:,}</div>
                                                    <div style="color: #666; font-size: 12px; margin-top: 3px;">${booking.budget:,} × {booking.get_travelers_display()}</div>
                                                </td>
                                                <td style="width: 50%; padding-left: 15px; border-left: 2px solid #e8e8e8;">
                                                    <div style="color: #999; font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 8px;">Trip Duration</div>
                                                    <div style="color: #000; font-size: 28px; font-weight: 700;">{booking.duration} Days</div>
                                                    <div style="color: #666; font-size: 12px; margin-top: 3px;">{booking.start_date.strftime('%b %d') if booking.start_date else 'Flexible'} - {booking.end_date.strftime('%b %d, %Y') if booking.end_date else 'Flexible'}</div>
                                                </td>
                                            </tr>
                                        </table>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                    
                    <!-- Quick Actions -->
                    <tr>
                        <td style="padding: 0 40px 30px;">
                            <div style="color: #999; font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 15px;">Quick Actions</div>
                            <table width="100%" cellpadding="0" cellspacing="0" border="0">
                                <tr>
                                    <td style="padding-right: 10px;">
                                        <a href="mailto:{booking.email}" style="display: block; background: #000; color: #fff; text-align: center; padding: 14px 20px; border-radius: 8px; text-decoration: none; font-size: 13px; font-weight: 700; letter-spacing: 0.5px;">
                                            ✉️ EMAIL CUSTOMER
                                        </a>
                                    </td>
                                    <td style="padding: 0 10px;">
                                        <a href="tel:{booking.phone}" style="display: block; background: #000; color: #fff; text-align: center; padding: 14px 20px; border-radius: 8px; text-decoration: none; font-size: 13px; font-weight: 700; letter-spacing: 0.5px;">
                                            📞 CALL CUSTOMER
                                        </a>
                                    </td>
                                    <td style="padding-left: 10px;">
                                        <a href="/admin/core/dashboard/{booking.id}/" style="display: block; background: #fafafa; color: #000; text-align: center; padding: 14px 20px; border-radius: 8px; text-decoration: none; font-size: 13px; font-weight: 700; letter-spacing: 0.5px; border: 2px solid #e8e8e8;">
                                            ⚙️ VIEW IN ADMIN
                                        </a>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                    
                    <!-- Customer Information -->
                    <tr>
                        <td style="padding: 0 40px 30px;">
                            <h2 style="margin: 0 0 20px 0; color: #000; font-size: 18px; font-weight: 700; padding-bottom: 10px; border-bottom: 2px solid #f0f0f0;">
                                Customer Information
                            </h2>
                            <table width="100%" cellpadding="0" cellspacing="0" border="0" style="background-color: #fafafa; border-radius: 8px; padding: 20px;">
                                <tr>
                                    <td style="padding: 8px 0; width: 50%;">
                                        <div style="color: #999; font-size: 11px; font-weight: 700; letter-spacing: 1px; text-transform: uppercase; margin-bottom: 5px;">Full Name</div>
                                        <div style="color: #000; font-size: 15px; font-weight: 600;">{booking.get_full_name()}</div>
                                    </td>
                                    <td style="padding: 8px 0;">
                                        <div style="color: #999; font-size: 11px; font-weight: 700; letter-spacing: 1px; text-transform: uppercase; margin-bottom: 5px;">Travelers</div>
                                        <div style="color: #000; font-size: 15px; font-weight: 600;">{booking.get_travelers_display()}</div>
                                    </td>
                                </tr>
                                <tr>
                                    <td style="padding: 8px 0;">
                                        <div style="color: #999; font-size: 11px; font-weight: 700; letter-spacing: 1px; text-transform: uppercase; margin-bottom: 5px;">Email</div>
                                        <div style="color: #333; font-size: 14px;"><a href="mailto:{booking.email}" style="color: #000; text-decoration: none;">{booking.email}</a></div>
                                    </td>
                                    <td style="padding: 8px 0;">
                                        <div style="color: #999; font-size: 11px; font-weight: 700; letter-spacing: 1px; text-transform: uppercase; margin-bottom: 5px;">Phone</div>
                                        <div style="color: #333; font-size: 14px;"><a href="tel:{booking.phone}" style="color: #000; text-decoration: none;">{booking.phone}</a></div>
                                    </td>
                                </tr>
                                <tr>
                                    <td style="padding: 8px 0;" colspan="2">
                                        <div style="color: #999; font-size: 11px; font-weight: 700; letter-spacing: 1px; text-transform: uppercase; margin-bottom: 5px;">Country</div>
                                        <div style="color: #000; font-size: 15px; font-weight: 600;">{booking.country}</div>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                    
                    <!-- Travel Details -->
                    <tr>
                        <td style="padding: 0 40px 30px;">
                            <h2 style="margin: 0 0 20px 0; color: #000; font-size: 18px; font-weight: 700; padding-bottom: 10px; border-bottom: 2px solid #f0f0f0;">
                                Travel Details
                            </h2>
                            <table width="100%" cellpadding="0" cellspacing="0" border="0">
                                <tr>
                                    <td style="padding: 10px 0; width: 50%;">
                                        <div style="color: #999; font-size: 11px; font-weight: 700; letter-spacing: 1px; text-transform: uppercase; margin-bottom: 5px;">Travel Style</div>
                                        <div style="color: #333; font-size: 14px;">{booking.get_travel_type_display() if booking.travel_type else 'Not specified'}</div>
                                    </td>
                                    <td style="padding: 10px 0;">
                                        <div style="color: #999; font-size: 11px; font-weight: 700; letter-spacing: 1px; text-transform: uppercase; margin-bottom: 5px;">Date Flexibility</div>
                                        <div style="color: #333; font-size: 14px;">{booking.get_date_flexibility_display()}</div>
                                    </td>
                                </tr>
                                <tr>
                                    <td style="padding: 10px 0;">
                                        <div style="color: #999; font-size: 11px; font-weight: 700; letter-spacing: 1px; text-transform: uppercase; margin-bottom: 5px;">Accommodation</div>
                                        <div style="color: #333; font-size: 14px;">{booking.get_accommodation_display() if booking.accommodation else 'Not specified'}</div>
                                    </td>
                                    <td style="padding: 10px 0;">
                                        <div style="color: #999; font-size: 11px; font-weight: 700; letter-spacing: 1px; text-transform: uppercase; margin-bottom: 5px;">Budget/Person</div>
                                        <div style="color: #000; font-size: 16px; font-weight: 700;">${booking.budget:,} USD</div>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                    
                    <!-- Selected Activities -->
                    <tr>
                        <td style="padding: 0 40px 30px;">
                            <h2 style="margin: 0 0 20px 0; color: #000; font-size: 18px; font-weight: 700; padding-bottom: 10px; border-bottom: 2px solid #f0f0f0;">
                                Selected Activities ({len(activities)} total)
                            </h2>
                            <div style="background-color: #fafafa; padding: 20px; border-radius: 8px;">
                                {activities_html}
                            </div>
                        </td>
                    </tr>
                    
                    <!-- Special Requests -->
                    {f'''<tr>
                        <td style="padding: 0 40px 30px;">
                            <h2 style="margin: 0 0 20px 0; color: #000; font-size: 18px; font-weight: 700; padding-bottom: 10px; border-bottom: 2px solid #f0f0f0;">
                                Special Requests
                            </h2>
                            <div style="padding: 20px; background-color: #fff8e1; border-left: 4px solid #ffc107; border-radius: 8px; color: #555; font-size: 14px; line-height: 1.7;">
                                {booking.special_requests}
                            </div>
                        </td>
                    </tr>''' if booking.special_requests else '<tr><td style="padding: 0 40px 30px;"><h2 style="margin: 0 0 20px 0; color: #000; font-size: 18px; font-weight: 700; padding-bottom: 10px; border-bottom: 2px solid #f0f0f0;">Special Requests</h2><div style="color: #999; font-style: italic; font-size: 14px;">No special requests provided</div></td></tr>'}
                    
                    <!-- Action Reminder -->
                    <tr>
                        <td style="padding: 0 40px 40px;">
                            <table width="100%" cellpadding="20" cellspacing="0" border="0" style="background: linear-gradient(135deg, #000000 0%, #1a1a1a 100%); border-radius: 8px;">
                                <tr>
                                    <td>
                                        <h3 style="margin: 0 0 15px 0; color: #fff; font-size: 16px; font-weight: 700;">
                                            ⏰ Action Required
                                        </h3>
                                        <p style="margin: 0; color: rgba(255, 255, 255, 0.9); font-size: 14px; line-height: 1.6;">
                                            Customer expects a personalized itinerary within 24 hours. Please review this booking and prepare a comprehensive proposal including accommodation options, detailed activities, and transparent pricing.
                                        </p>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                    
                    <!-- Footer -->
                    <tr>
                        <td style="padding: 25px 40px; text-align: center; background-color: #fafafa; border-top: 1px solid #e8e8e8;">
                            <p style="margin: 0; color: #999; font-size: 12px;">
                                Automated notification from Discover Rwanda Booking System
                            </p>
                            <p style="margin: 10px 0 0 0; color: #999; font-size: 12px;">
                                Booking ID: {booking.get_booking_id()} | Customer: {booking.email}
                            </p>
                        </td>
                    </tr>
                    
                </table>
                
            </td>
        </tr>
    </table>
    
</body>
</html>
"""
        
        # Plain text version as fallback
        text_message = f"""
╔══════════════════════════════════════════╗
║     NEW BOOKING REQUEST RECEIVED         ║
╚══════════════════════════════════════════╝

Booking ID: {booking.get_booking_id()}
Submission: {booking.created_at.strftime('%B %d, %Y at %I:%M %p')}

═══════════════════════════════════════════
PRIORITY INFORMATION
═══════════════════════════════════════════

Total Trip Value: ${total_budget:,} (${booking.budget:,} × {booking.get_travelers_display()})
Duration: {booking.duration} days
Travel Dates: {booking.start_date.strftime('%b %d') if booking.start_date else 'Flexible'} - {booking.end_date.strftime('%b %d, %Y') if booking.end_date else 'Flexible'}

═══════════════════════════════════════════
CUSTOMER INFORMATION
═══════════════════════════════════════════

Name: {booking.get_full_name()}
Email: {booking.email}
Phone: {booking.phone}
Country: {booking.country}
Travelers: {booking.get_travelers_display()}

═══════════════════════════════════════════
TRAVEL DETAILS
═══════════════════════════════════════════

Travel Style: {booking.get_travel_type_display() if booking.travel_type else 'Not specified'}
Date Flexibility: {booking.get_date_flexibility_display()}
Accommodation: {booking.get_accommodation_display() if booking.accommodation else 'Not specified'}
Budget per Person: ${booking.budget:,} USD

═══════════════════════════════════════════
SELECTED ACTIVITIES ({len(activities)} total)
═══════════════════════════════════════════

{chr(10).join('• ' + activity.replace('-', ' ').title() for activity in activities) if activities else '• None selected'}

═══════════════════════════════════════════
SPECIAL REQUESTS
═══════════════════════════════════════════

{booking.special_requests if booking.special_requests else 'None provided'}

═══════════════════════════════════════════
QUICK ACTIONS
═══════════════════════════════════════════

View in Admin: /admin/core/travelbooking/{booking.id}/
Email Customer: {booking.email}
Call Customer: {booking.phone}

⏰ ACTION REQUIRED: Customer expects itinerary within 24 hours

---
Automated notification from Discover Rwanda Booking System
"""
        
        # Send to admin with HTML
        from django.core.mail import EmailMultiAlternatives
        
        admin_email = getattr(settings, 'ADMIN_EMAIL', settings.DEFAULT_FROM_EMAIL)
        
        email = EmailMultiAlternatives(
            subject=subject,
            body=text_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[admin_email],
            reply_to=[booking.email],
        )
        email.attach_alternative(html_message, "text/html")
        email.send(fail_silently=False)
        
        print(f"✅ Premium admin notification sent to {admin_email}")
        return True
        
    except Exception as e:
        print(f"❌ Error sending admin email: {e}")
        import traceback
        traceback.print_exc()
        return False


# Class-based views for dashboard (optional)
class BookingListView(ListView):
    """List view of all bookings (requires login)"""
    model = TravelBooking
    template_name = 'core/booking_list.html'
    context_object_name = 'bookings'
    paginate_by = 25
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by status
        status = self.request.GET.get('status')
        if status == 'processed':
            queryset = queryset.filter(is_processed=True)
        elif status == 'pending':
            queryset = queryset.filter(is_processed=False)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['total_count'] = TravelBooking.objects.count()
        context['pending_count'] = TravelBooking.objects.filter(is_processed=False).count()
        context['processed_count'] = TravelBooking.objects.filter(is_processed=True).count()
        return context


class BookingDetailView(DetailView):
    """Detail view of a single booking"""
    model = TravelBooking
    template_name = 'core/booking_detail.html'
    context_object_name = 'booking'



def dashboard(request):
    bookings = TravelBooking.objects.all().order_by('-id')  # get all bookings
    context = {
        'bookings': bookings
    }
    return render(request, 'adminpanel/dashboard.html', context)

def booking_pdf(request, pk):
    booking = get_object_or_404(TravelBooking, pk=pk)

    template = get_template("adminpanel/booking_pdf.html")
    html = template.render({"booking": booking})

    result = io.BytesIO()
    pdf = pisa.CreatePDF(io.StringIO(html), dest=result)

    if pdf.err:
        return HttpResponse("PDF generation error", status=500)

    response = HttpResponse(result.getvalue(), content_type="application/pdf")
    response["Content-Disposition"] = f'inline; filename="booking_{booking.pk}.pdf"'
    return response

def booking_view(request, pk):
    booking = get_object_or_404(TravelBooking, pk=pk)

    # Calculate total and per day budget
    total_budget = booking.budget * booking.duration
    per_day_budget = booking.budget / booking.duration if booking.duration else 0

    context = {
        'booking': booking,
        'total_budget': total_budget,
        'per_day_budget': per_day_budget,
    }

    return render(request, 'adminpanel/booking_view.html', context)


# Edit booking
def booking_edit(request, pk):
    booking = get_object_or_404(TravelBooking, pk=pk)
    if request.method == 'POST':
        form = TravelBookingForm(request.POST, instance=booking)
        if form.is_valid():
            form.save()
            return redirect('dashboard')  # or your dashboard page
    else:
        form = TravelBookingForm(instance=booking)
    return render(request, 'adminpanel/booking_edit.html', {'form': form, 'booking': booking})

# Delete booking
def booking_delete(request, pk):
    booking = get_object_or_404(TravelBooking, pk=pk)
    if request.method == 'POST':
        booking.delete()
        return redirect('dashboard')
    return render(request, 'booking_confirm_delete.html', {'booking': booking})