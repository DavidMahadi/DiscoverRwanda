from django import forms
from .models import TravelBooking
import json



import json
from django import forms
from .models import TravelBooking


class TravelBookingForm(forms.ModelForm):

    ACTIVITY_CHOICES = [
        # Wildlife & Nature
        ('gorilla-trekking', 'Gorilla Trekking'),
        ('golden-monkey', 'Golden Monkey Tracking'),
        ('chimpanzee', 'Chimpanzee Trekking'),
        ('big-five', 'Big Five Safari'),
        ('boat-safari', 'Boat Safari'),
        ('bird-watching', 'Bird Watching'),
        ('canopy-walk', 'Canopy Walk'),
        ('nature-walks', 'Guided Nature Walks'),
        ('waterfall', 'Waterfall Hikes'),

        # Adventure & Outdoor
        ('volcano-hiking', 'Volcano Hiking'),
        ('mountain-climbing', 'Mountain Climbing'),
        ('kayaking', 'Kayaking'),
        ('cycling', 'Congo Nile Trail'),
        ('fishing', 'Sport Fishing'),
        ('zip-lining', 'Zip Lining'),

        # Water & Leisure
        ('sunset-cruise', 'Sunset Cruise'),
        ('swimming-beach', 'Swimming & Beach'),
        ('spa-wellness', 'Spa & Wellness'),
        ('yoga-meditation', 'Yoga & Meditation'),
        ('hot-springs', 'Hot Springs'),
        ('golf', 'Golf'),

        # Cultural & Educational
        ('genocide-memorial', 'Genocide Memorial'),
        ('cultural-villages', 'Cultural Villages'),
        ('traditional-dance', 'Traditional Dance'),
        ('cooking-class', 'Cooking Classes'),
        ('art-workshops', 'Art Workshops'),
        ('museums-galleries', 'Museums & Galleries'),
        ('coffee-tours', 'Coffee Tours'),
        ('tea-plantation', 'Tea Plantations'),
        ('market-tours', 'Market Tours'),

        # Urban & Modern
        ('kigali-tour', 'Kigali City Tour'),
        ('fine-dining', 'Fine Dining'),
        ('street-food', 'Street Food Tours'),
        ('nightlife-music', 'Nightlife & Music'),
        ('photography-tours', 'Photography Tours'),
        ('shopping', 'Shopping'),
    ]

    # Activities
    activities = forms.MultipleChoiceField(
        required=True,
        choices=ACTIVITY_CHOICES,
        widget=forms.CheckboxSelectMultiple
    )

    # Dates
    start_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'})
    )

    end_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'})
    )

    # Auto-calculated
    duration = forms.IntegerField(
        required=False,
        disabled=True,
        label="Duration (days)"
    )

    # System field
    status = forms.CharField(
        required=False,
        disabled=True
    )

    class Meta:
        model = TravelBooking
        fields = [
            'first_name', 'last_name', 'email', 'phone', 'country',
            'travelers', 'travel_type', 'start_date', 'end_date',
            'date_flexibility', 'duration',
            'activities',
            'accommodation', 'budget', 'special_requests',
            'status'
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # required fields
        for name, field in self.fields.items():
            if name not in ['status', 'duration']:
                field.required = True

        # preload activities (edit mode)
        if self.instance and self.instance.activities:
            try:
                self.initial['activities'] = json.loads(self.instance.activities)
            except:
                self.initial['activities'] = []

        # preload status
        if self.instance:
            self.fields['status'].initial = self.instance.status

    def clean(self):
        cleaned_data = super().clean()

        start = cleaned_data.get('start_date')
        end = cleaned_data.get('end_date')

        # auto duration
        if start and end:
            if end < start:
                self.add_error('end_date', "End date cannot be before start date")
            else:
                days = (end - start).days
                if days == 0:
                    days = 1
                cleaned_data['duration'] = days
        else:
            self.add_error('start_date', "Start date is required")
            self.add_error('end_date', "End date is required")

        # activities cannot be empty
        if not cleaned_data.get('activities'):
            self.add_error('activities', "Please select at least one activity")

        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)

        # JSON storage
        instance.activities = json.dumps(
            self.cleaned_data.get('activities', [])
        )

        # duration
        instance.duration = self.cleaned_data.get('duration', instance.duration)

        if commit:
            instance.save()
        return instance