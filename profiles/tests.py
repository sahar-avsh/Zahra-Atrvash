from django.test import TestCase, Client
from django.urls import reverse
import datetime
import pytz

# Create your tests here.
from .models import OwnerToParticipantReview, Profile, ProfileFollowRequest, ProfileJoinOfferRequest, ProfileReview
from .forms import ProfileModelForm
from offers.models import Offer
from django.contrib.auth.models import User

tz = pytz.timezone('Europe/Istanbul')
now = datetime.datetime.now().replace(tzinfo=tz)

class ProfileModelFormTest(TestCase):
  def test_profile_model_form(self):
    form_data = {
    'f_name': 'TestFirstname',
    'l_name': 'TestLastName', 
    'birthday': now - datetime.timedelta(days=365 * 18), 
    'occupation': 'TestOccupation', 
    'education': 'High School Diploma', 
    'description': 'TestDescription',
    'location': '',
    'image': ''
    }
    form = ProfileModelForm(data=form_data)
    self.assertTrue(form.is_valid())

  def test_profile_model_form_invalid_f_name(self):
    form_data = {
    'f_name': 'T',
    'l_name': 'TestLastName', 
    'birthday': now - datetime.timedelta(days=365 * 18), 
    'occupation': 'TestOccupation', 
    'education': 'High School Diploma', 
    'description': 'TestDescription'
    }
    form = ProfileModelForm(data=form_data)
    self.assertFalse(form.is_valid())

  def test_profile_model_form_invalid_l_name(self):
    form_data = {
    'f_name': 'TestFirstname',
    'l_name': 'T', 
    'birthday': now - datetime.timedelta(days=365 * 18), 
    'occupation': 'TestOccupation', 
    'education': 'High School Diploma', 
    'description': 'TestDescription'
    }
    form = ProfileModelForm(data=form_data)
    self.assertFalse(form.is_valid())

  def test_profile_model_form_invalid_birthday(self):
    form_data = {
    'f_name': 'TestFirstname',
    'l_name': 'TestLastName', 
    'birthday': now + datetime.timedelta(days=1), 
    'occupation': 'TestOccupation', 
    'education': 'High School Diploma', 
    'description': 'TestDescription'
    }
    form = ProfileModelForm(data=form_data)
    self.assertFalse(form.is_valid())

class TestProfileViews(TestCase):
  @classmethod
  def setUp(self):
    self.user_1 = User.objects.create_user(username='TestUser1', password='Test')
    self.user_2 = User.objects.create_user(username='TestUser2', password='Test')
    self.user_3 = User.objects.create_user(username='TestUser3', password='Test')
    self.profile_1 = Profile.objects.create(user=self.user_1, f_name='TestFirstname1', l_name='TestLastname1')
    self.profile_2 = Profile.objects.create(user=self.user_2, f_name='TestFirstname2', l_name='TestLastname2')
    self.profile_3 = Profile.objects.create(user=self.user_3, f_name='TestFirstname3', l_name='TestLastname3')
    self.offer_1 = Offer.objects.create(
    owner=self.profile_1, 
    title='TestOffer1', 
    start_date=now + datetime.timedelta(hours=1), 
    end_date=now + datetime.timedelta(hours=2), 
    credit=1, 
    capacity=5, 
    app_deadline=now + datetime.timedelta(hours=0.5), 
    cancel_deadline=now + datetime.timedelta(hours=0.7), 
    offer_format='Offline', 
    offer_type='Service',
    description='TestOffer1'
    )
    self.offer_1.participants.add(self.profile_2)
    self.client = Client()
  
  def test_profile_outlook_view(self):
    login = self.client.login(username='TestUser1', password='Test')
    response = self.client.get(reverse('profile_look', kwargs={'pk': self.profile_1.id}))
    self.assertEqual(response.status_code, 200)
    self.assertTemplateUsed(response, 'profiles/outlook.html')

  def test_profile_notifications_view(self):
    login = self.client.login(username='TestUser1', password='Test')
    response = self.client.get(reverse('notifications'))
    self.assertEqual(response.status_code, 200)
    self.assertTemplateUsed(response, 'profiles/notifications.html')

  def test_profile_activities_view(self):
    login = self.client.login(username='TestUser1', password='Test')
    response = self.client.get(reverse('activity_background', kwargs={'profileID': self.profile_1.id}))
    self.assertEqual(response.status_code, 200)
    self.assertTemplateUsed(response, 'profiles/activity_background.html')

  def test_profile_friends_view(self):
    login = self.client.login(username='TestUser1', password='Test')
    response = self.client.get(reverse('friends', kwargs={'profileID': self.profile_1.id}))
    self.assertEqual(response.status_code, 200)
    self.assertTemplateUsed(response, 'profiles/friends.html')

  def test_rate_finished_offer_view_saves_valid_object(self):
    login = self.client.login(username='TestUser2', password='Test')
    response = self.client.get(reverse('rate_offer', kwargs={'offerID': self.offer_1.id}))
    self.assertEqual(response.status_code, 200)
    self.assertTemplateUsed(response, 'profiles/rate_offer_form.html')
    data = {
    'rating': 3,
    'done': True,
    'text': 'TestReview'
    }
    response = self.client.post(reverse('rate_offer', kwargs={'offerID': self.offer_1.id}), data)
    self.assertTrue(ProfileReview.objects.get(review_giver=self.profile_2, offer=self.offer_1))
    self.assertRedirects(response, reverse('home_page'))

  def test_rate_participant_view_saves_valid_object(self):
    login = self.client.login(username='TestUser1', password='Test')
    response = self.client.get(reverse('rate_participant', kwargs={'offerID': self.offer_1.id, 'participantID': self.profile_2.id}))
    self.assertEqual(response.status_code, 200)
    self.assertTemplateUsed(response, 'profiles/rate_participant_form.html')
    data = {
    'rating': 3,
    'text': 'TestReview'
    }
    response = self.client.post(reverse('rate_participant', kwargs={'offerID': self.offer_1.id, 'participantID': self.profile_2.id}), data)
    self.assertTrue(OwnerToParticipantReview.objects.get(offer=self.offer_1, participant=self.profile_2))
    self.assertRedirects(response, reverse('offer_look', kwargs={'pk': self.offer_1.id}))

  def test_send_join_request_saves_valid_object(self):
    login = self.client.login(username='TestUser3', password='Test')
    response = self.client.get(reverse('send_join_request', kwargs={'offerID': self.offer_1.id}))
    self.assertTrue(ProfileJoinOfferRequest.objects.get(profile=self.profile_3, offer=self.offer_1))
    self.assertRedirects(response, reverse('offer_look', kwargs={'pk': self.offer_1.id}))

  def test_send_follow_request_saves_valid_object(self):
    login = self.client.login(username='TestUser3', password='Test')
    response = self.client.get(reverse('send_follow_request', kwargs={'profileID': self.profile_1.id}))
    self.assertTrue(ProfileFollowRequest.objects.get(profile_id=self.profile_3, following_profile_id=self.profile_1))
    self.assertRedirects(response, reverse('profile_look', kwargs={'pk': self.profile_1.id}))
  
  def tearDown(self):
    return super().tearDown()

