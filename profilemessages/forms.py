from django import forms
from profilemessages.models import ProfileMessage

class ProfileMessageForm(forms.ModelForm):
  class Meta:
    model = ProfileMessage
    fields = ['title', 'body']

class MessageSearchForm(forms.Form):
  text = forms.CharField(widget=forms.TextInput(), required=False)