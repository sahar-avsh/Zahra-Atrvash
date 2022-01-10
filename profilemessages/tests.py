from django.test import TestCase, Client
from django.urls import reverse

# Create your tests here.
from .models import ProfileMessage
from .forms import ProfileMessageForm
from profiles.models import Profile
from django.contrib.auth.models import User

class ProfileMessageFormTest(TestCase):
  def test_profile_message_form(self):
    form_data = {
    'title': 'TestTitle',
    'body': 'TestBody'
    }
    form = ProfileMessageForm(data=form_data)
    self.assertTrue(form.is_valid())

  def test_profile_model_form_invalid_title(self):
    form_data = {
    'title': 'T',
    'body': 'TestBody'
    }
    form = ProfileMessageForm(data=form_data)
    self.assertFalse(form.is_valid())

  def test_profile_model_form_invalid_body(self):
    form_data = {
    'title': 'TestTitle',
    'body': 'T'
    }
    form = ProfileMessageForm(data=form_data)
    self.assertFalse(form.is_valid())

class TestProfileMessageViews(TestCase):
  @classmethod
  def setUp(self):
    self.user_1 = User.objects.create_user(username='TestUser1', password='Test')
    self.user_2 = User.objects.create_user(username='TestUser2', password='Test')
    self.profile_1 = Profile.objects.create(user=self.user_1, f_name='TestFirstname1', l_name='TestLastname1')
    self.profile_2 = Profile.objects.create(user=self.user_2, f_name='TestFirstname2', l_name='TestLastname2')
    self.client = Client()
  
  def test_send_message_view(self):
    login = self.client.login(username='TestUser1', password='Test')
    response = self.client.get(reverse('send_message', kwargs={'profileID': self.profile_2.id}))
    self.assertEqual(response.status_code, 200)
    self.assertTemplateUsed(response, 'messages/send_message.html')
    data = {
      'title': 'TestTitle',
      'body': 'TestBody'
    }
    response = self.client.post(reverse('send_message', kwargs={'profileID': self.profile_2.id}), data)
    self.assertTrue(ProfileMessage.objects.get(message_to=self.profile_2, message_from=self.profile_1))
    self.assertRedirects(response, reverse('home_page'))

  def test_inbox_view(self):
    login = self.client.login(username='TestUser1', password='Test')
    response = self.client.get(reverse('inbox'))
    self.assertEqual(response.status_code, 200)
    self.assertTemplateUsed(response, 'messages/inbox_view.html')

  def test_sent_messages_view(self):
    login = self.client.login(username='TestUser1', password='Test')
    response = self.client.get(reverse('sent_messages'))
    self.assertEqual(response.status_code, 200)
    self.assertTemplateUsed(response, 'messages/sent_messages_view.html')

  def tearDown(self):
    return super().tearDown()

