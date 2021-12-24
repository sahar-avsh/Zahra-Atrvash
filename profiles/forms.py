from django import forms
from allauth.account.forms import SignupForm, LoginForm
from django.contrib.auth.models import User

from profiles.models import Profile

class DateInput(forms.DateInput):
  input_type = 'date'

class ProfileModelForm(forms.ModelForm):
  class Meta:
    model = Profile
    fields = [
      'image',
      'f_name',
      'l_name',
      'birthday',
      'occupation',
      'loc_long',
      'loc_ltd',
      'education',
      'description'
    ]

    widgets = {
      'birthday': DateInput(),
    }

  def clean_f_name(self):
    data = self.cleaned_data.get('f_name')
    if len(data) < 2:
      raise forms.ValidationError('This is not long enough. (That\'s what she said)')
    return data

  def clean_offers(self):
    data = self.cleaned_data.get('offers')
    offer_owners = [o.owner.id for o in data]
    if self.id in offer_owners:
      raise forms.ValidationError('User cannot participate in own offer.')
    return data

class CustomSignupForm(SignupForm):
  email = forms.EmailField()
  first_name = forms.CharField(max_length=30, label='First Name')
  last_name = forms.CharField(max_length=30, label='Last Name')
 
  class Meta:
    model = User
    fields = ('first_name', 'last_name', 'email', 'password1', 'password2')


    def save(self, commit=True):
      user = super().save(commit=False)

      user.email = self.cleaned_data['email']
      user.first_name = self.cleaned_data['first_name']
      user.last_name = self.cleaned_data['last_name']

      if commit:
          user.save()
      return user

class CustomLoginForm(LoginForm):
  login = forms.EmailField()
  class Meta:
    model = User
    fields = ('login', 'password')


  def login(self, *args, **kwargs):

    # Add your own processing here.

    # You must return the original result.
    return super(CustomLoginForm, self).login(*args, **kwargs)