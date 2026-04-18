import json
from django import forms
from .models import TravelBooking


class TravelBookingForm(forms.ModelForm):

    # ─────────────────────────────────────────────────────────────
    # Every value here matches EXACTLY the value="..." in contact.html
    # ─────────────────────────────────────────────────────────────
    ACTIVITY_CHOICES = [
        # Wildlife (data-category="wildlife")
        ('gorilla-trekking',   'Gorilla Trekking'),
        ('golden-monkey',      'Golden Monkey Tracking'),
        ('chimpanzee',         'Chimpanzee Trekking'),

        # Safari (data-category="safari")
        ('big-five',           'Big Five Safari'),
        ('boat-safari',        'Boat Safari'),
        ('bird-watching',      'Bird Watching'),

        # Nature (data-category="nature")
        ('canopy-walk',        'Canopy Walk'),
        ('guided-walks',       'Guided Nature Walks'),
        ('waterfall-hikes',    'Waterfall Hikes'),
        ('volcano-hiking',     'Volcano Hiking'),
        ('mountain-climbing',  'Mountain Climbing'),

        # Lake Kivu (data-category="lake")
        ('kayaking',           'Kayaking'),
        ('congo-nile',         'Congo Nile Trail'),
        ('sport-fishing',      'Sport Fishing'),
        ('zip-lining',         'Zip Lining'),
        ('sunset-cruise',      'Sunset Cruise'),
        ('swimming-beach',     'Swimming & Beach'),
        ('spa-wellness',       'Spa & Wellness'),
        ('yoga-meditation',    'Yoga & Meditation'),
        ('hot-springs',        'Hot Springs'),
        ('golf',               'Golf'),

        # Cultural (data-category="cultural")
        ('genocide-memorial',  'Genocide Memorial'),
        ('cultural-villages',  'Cultural Villages'),
        ('traditional-dance',  'Traditional Dance'),
        ('cooking-classes',    'Cooking Classes'),
        ('art-workshops',      'Art Workshops'),
        ('museums-galleries',  'Museums & Galleries'),
        ('coffee-tours',       'Coffee Tours'),
        ('tea-plantations',    'Tea Plantations'),
        ('market-tours',       'Market Tours'),

        # Kigali City (data-category="city")
        ('kigali-tour',        'Kigali City Tour'),
        ('fine-dining',        'Fine Dining'),
        ('street-food',        'Street Food Tours'),
        ('nightlife-music',    'Nightlife & Music'),
        ('photography-tours',  'Photography Tours'),
        ('shopping',           'Shopping'),
    ]

    activities = forms.MultipleChoiceField(
        required=True,
        choices=ACTIVITY_CHOICES,
        widget=forms.CheckboxSelectMultiple,
        error_messages={'required': 'Please select at least one activity.'}
    )

    start_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'})
    )

    end_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'})
    )

    # HiddenInput so Django accepts the value from JS without blocking validation
    duration = forms.IntegerField(
        required=False,
        widget=forms.HiddenInput()
    )

    status = forms.CharField(
        required=False,
        widget=forms.HiddenInput()
    )

    class Meta:
        model = TravelBooking
        fields = [
            'first_name', 'last_name', 'email', 'phone', 'country',
            'travelers', 'travel_type', 'start_date', 'end_date',
            'date_flexibility', 'duration',
            'activities',
            'accommodation', 'budget', 'special_requests',
            'status',
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for name, field in self.fields.items():
            if name not in ('status', 'duration', 'special_requests'):
                field.required = True

        # Pre-populate activities when editing an existing booking
        if self.instance and self.instance.pk and self.instance.activities:
            try:
                self.initial['activities'] = json.loads(self.instance.activities)
            except Exception:
                self.initial['activities'] = []

    def clean(self):
        cleaned_data = super().clean()

        start = cleaned_data.get('start_date')
        end   = cleaned_data.get('end_date')

        if start and end:
            if end < start:
                self.add_error('end_date', 'End date cannot be before start date.')
            else:
                days = (end - start).days or 1
                cleaned_data['duration'] = days
        else:
            if not start:
                self.add_error('start_date', 'Start date is required.')
            if not end:
                self.add_error('end_date', 'End date is required.')

        if not cleaned_data.get('activities'):
            self.add_error('activities', 'Please select at least one activity.')

        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.activities = json.dumps(self.cleaned_data.get('activities', []))
        instance.duration   = self.cleaned_data.get('duration') or instance.duration
        if commit:
            instance.save()
        return instance
