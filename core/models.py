from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
import json


class TravelBooking(models.Model):

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processed', 'Processed'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
    ]

    TRAVEL_TYPE_CHOICES = [
        ('solo', 'Solo Travel'),
        ('family', 'Family Travel'),
        ('couple', 'Couple Getaway'),
        ('group', 'Group Adventure'),
    ]

    TRAVELERS_CHOICES = [
        ('1', '1 Traveler (Solo)'),
        ('2', '2 Travelers (Couple)'),
        ('3', '3 Travelers'),
        ('4', '4 Travelers'),
        ('5', '5 Travelers'),
        ('6', '6 Travelers'),
        ('7', '7 Travelers'),
        ('8', '8 Travelers'),
        ('9-15', '9-15 Travelers (Group)'),
        ('16+', '16+ Travelers (Large Group)'),
    ]

    FLEXIBILITY_CHOICES = [
        ('fixed', 'Fixed dates - cannot change'),
        ('flexible-few-days', 'Flexible ± 2-3 days'),
        ('flexible-week', 'Flexible ± 1 week'),
        ('flexible-month', 'Flexible - planning months in advance'),
    ]

    ACCOMMODATION_CHOICES = [
        ('luxury', '5-Star Luxury'),
        ('boutique', 'Boutique Lodges'),
        ('mid-range', 'Mid-Range Hotels'),
        ('budget', 'Budget-Friendly'),
    ]

    # Personal Info
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(db_index=True)
    phone = models.CharField(max_length=20)
    country = models.CharField(max_length=100)
    travelers = models.CharField(max_length=20, choices=TRAVELERS_CHOICES)

    # Travel Info
    travel_type = models.CharField(max_length=20, choices=TRAVEL_TYPE_CHOICES, blank=True, null=True)
    start_date = models.DateField(blank=True, null=True)
    end_date = models.DateField(blank=True, null=True)
    date_flexibility = models.CharField(max_length=30, choices=FLEXIBILITY_CHOICES, default='flexible-month')
    duration = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(21)], default=7)

    # Activities (SQLite-safe JSON storage)
    activities = models.TextField(default='[]', blank=True)

    # Accommodation & Budget
    accommodation = models.CharField(max_length=20, choices=ACCOMMODATION_CHOICES, blank=True, null=True)
    budget = models.IntegerField(validators=[MinValueValidator(1000), MaxValueValidator(15000)], default=5000)

    # Special Requests
    special_requests = models.TextField(blank=True)

    # System
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    is_processed = models.BooleanField(default=False)
    processed_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f"{self.get_full_name()} - {self.email}"

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"

    def get_booking_id(self):
        return f"BOOK-{self.pk}"

    def get_activities_list(self):
        try:
            return json.loads(self.activities)
        except:
            return []

    # Workflow
    def mark_as_processed(self):
        self.is_processed = True
        self.processed_at = timezone.now()
        self.status = 'processed'
        self.save(update_fields=['is_processed', 'processed_at', 'status'])

    def mark_as_confirmed(self):
        self.status = 'confirmed'
        self.save(update_fields=['status'])

    def cancel_booking(self):
        self.status = 'cancelled'
        self.save(update_fields=['status'])

    
            

class Booking(models.Model):
    booking_id = models.CharField(max_length=20)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField()
    travelers = models.IntegerField()
    date = models.DateField()
    budget = models.CharField(max_length=50)
    status = models.CharField(max_length=20, default="Pending")

    def __str__(self):
        return self.booking_id
    
    @property
    def customer_name(self):
        return f"{self.first_name} {self.last_name}"