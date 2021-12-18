from django import forms

from profiles.models import Profile

""" class ProfileForm(forms.Form):
  name = forms.CharField() """

class ProfileModelForm(forms.ModelForm):
  class Meta:
    model = Profile
    fields = [
      'image',
      'f_name',
      'l_name',
      'email',
      'birthday',
      'occupation',
      'loc_long',
      'loc_ltd',
      'education',
      'description'
    ]

  def clean_f_name(self):
    data = self.cleaned_data.get('f_name')
    if len(data) < 2:
      raise forms.ValidationError('This is not long enough. (That\'s what she said)')
    return data