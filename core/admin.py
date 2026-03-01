# myapp/admin.py
from django.contrib import admin
from .models import TravelBooking, Booking

admin.site.register(TravelBooking)
admin.site.register(Booking)