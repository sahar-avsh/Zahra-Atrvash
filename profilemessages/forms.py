from django import forms
from profilemessages.models import ProfileMessage

class ProfileMessageForm(forms.ModelForm):
  class Meta:
    model = ProfileMessage
    fields = ['title', 'body']

  def clean_title(self):
    data = self.cleaned_data.get('title')
    if len(data) < 2:
      raise forms.ValidationError('This is not long enough.')
    return data

  def clean_body(self):
    data = self.cleaned_data.get('body')
    if len(data) < 2:
      raise forms.ValidationError('This is not long enough.')
    return data
  

class MessageSearchForm(forms.Form):
  text = forms.CharField(widget=forms.TextInput(), required=False)