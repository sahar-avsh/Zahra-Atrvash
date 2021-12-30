from django import forms
from profilemessages.models import ProfileMessage

class ProfileMessageForm(forms.ModelForm):
  class Meta:
    model = ProfileMessage
    fields = ['title', 'body']
