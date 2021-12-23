from django import forms
from django.forms.widgets import DateTimeInput

from offers.models import Offer

class DateTimeInput(forms.DateTimeInput):
  input_type = 'datetime-local'

class OfferModelForm(forms.ModelForm):
  class Meta:
    model = Offer
    fields = [
      'image',
      'title',
      'loc_long',
      'loc_ltd',
      'start_date',
      'end_date',
      'capacity',
      'app_deadline',
      'cancel_deadline',
      'offer_format',
      'offer_type',
      'description',
      'tags'
    ]
    widgets = {
      'start_date': DateTimeInput(),
      'end_date': DateTimeInput(),
      'app_deadline': DateTimeInput(),
      'cancel_deadline': DateTimeInput()
    }

  # def clean_title(self):
  #   data = self.cleaned_data.get('title')
  #   if len(data) < 2:
  #     raise forms.ValidationError('This is not long enough. (That\'s what she said)')
  #   return data

  # def clean_end_date(self):
  #   start_date = self.cleaned_data.get('start_date')
  #   end_date = self.cleaned_data.get('end_date')

  #   if end_date - start_date <= 0:
  #     raise forms.ValidationError('End date must be later than start date.')
  #   return end_date

  # def clean_app_deadline(self):
  #   app_deadline = self.cleaned_data.get('app_deadline')
  #   start_date = self.cleaned_data.get('start_date')

  #   if app_deadline - start_date <= 0:
  #     raise forms.ValidationError('Application deadline must be before start date.')
  #   return app_deadline

  # def clean_cancel_deadline(self):
  #   app_deadline = self.cleaned_data.get('app_deadline')
  #   cancel_deadline = self.cleaned_data.get('cancel_deadline')

  #   if cancel_deadline - app_deadline <= 0:
  #     raise forms.ValidationError('Cancellation deadline must be later than application deadline.')
  #   return cancel_deadline