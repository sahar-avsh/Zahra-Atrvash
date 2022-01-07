from django import forms
from django.forms import widgets
from django.forms.widgets import DateTimeInput

# from mapbox_location_field.forms import LocationField
from mapwidgets.widgets import GooglePointFieldWidget
from django.contrib.gis import forms as gis_forms

from offers.models import Offer

import pytz
import datetime

class DateTimeInput(forms.DateTimeInput):
  input_type = 'datetime-local'

class OfferModelForm(forms.ModelForm):
  class Meta:
    model = Offer
    fields = [
      'image',
      'title',
      'start_date',
      'end_date',
      'capacity',
      'app_deadline',
      'cancel_deadline',
      'offer_format',
      'offer_type',
      'description',
      'location',
    ]
    widgets = {
      'start_date': DateTimeInput(),
      'end_date': DateTimeInput(),
      'app_deadline': DateTimeInput(),
      'cancel_deadline': DateTimeInput(),
      'location': GooglePointFieldWidget,
    }

  def clean_title(self):
    data = self.cleaned_data.get('title')
    if len(data) < 2:
      raise forms.ValidationError('This is not long enough.')
    return data

  def start_date(self):
    start_date = self.cleaned_data.get('start_date')
    tz = pytz.timezone('Europe/Istanbul')
    now = datetime.datetime.now().replace(tzinfo=tz)
    if start_date < now:
      raise forms.ValidationError('Start date must be later than now.')
    return start_date

  def clean_end_date(self):
    start_date = self.cleaned_data.get('start_date')
    end_date = self.cleaned_data.get('end_date')

    if start_date:
      if end_date <= start_date:
        raise forms.ValidationError('End date must be later than start date.')
      return end_date
    else:
      raise forms.ValidationError('Please fix other errors before moving onto end date.')

  def clean_app_deadline(self):
    app_deadline = self.cleaned_data.get('app_deadline')
    start_date = self.cleaned_data.get('start_date')

    if start_date <= app_deadline:
      raise forms.ValidationError('Application deadline must be before start date.')
    return app_deadline

  def clean_cancel_deadline(self):
    app_deadline = self.cleaned_data.get('app_deadline')
    cancel_deadline = self.cleaned_data.get('cancel_deadline')
    start_date = self.cleaned_data.get('start_date')

    if app_deadline and start_date:
      if cancel_deadline < app_deadline:
        raise forms.ValidationError('Cancellation deadline must be later than application deadline.')
      elif start_date < cancel_deadline:
        raise forms.ValidationError('Cancellation deadline must be before start date.')
      return cancel_deadline
    else:
      raise forms.ValidationError('Please fix other errors before moving onto cancellation deadline.')

  def clean_capacity(self):
    capacity = self.cleaned_data.get('capacity')

    if capacity < 1:
      raise forms.ValidationError('Capacity must be 1 or higher.')
    return capacity
      

class ApproveForm(forms.ModelForm):
  CHOICES_DONE = [
  ('Approve', 'Approve'),
  ('Decline', 'Decline')
  ]
  offer_done = forms.ChoiceField(choices=CHOICES_DONE, widget=forms.RadioSelect)
  class Meta:
    model = Offer
    fields = []

class OfferFilterForm(forms.Form):
  title = forms.CharField(widget=forms.TextInput(), required=False)
  start_date = forms.DateTimeField(widget=forms.DateTimeInput(attrs={'type': 'datetime-local'}), required=False)
  distance = forms.IntegerField(required=False)
  credit = forms.IntegerField(required=False)
  tags = forms.CharField(required=False)
  new_location = gis_forms.PointField(required=False, widget=GooglePointFieldWidget)
  CHOICES_TYPE = [
  ('All', 'All'),
  ('Service', 'Service'),
  ('Event', 'Event')
  ]
  offer_type = forms.ChoiceField(choices=CHOICES_TYPE)
  CHOICES_FORMAT = [
  ('All', 'All'),
  ('Online', 'Online'),
  ('Offline', 'Offline')
  ]
  offer_format = forms.ChoiceField(choices=CHOICES_FORMAT)