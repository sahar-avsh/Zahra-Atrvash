from django.test import TestCase, Client
from django.urls import reverse
import datetime
import pytz

# Create your tests here.
from .models import Offer
from .forms import OfferModelForm
from profiles.models import Profile
from django.contrib.auth.models import User

tz = pytz.timezone('Europe/Istanbul')
now = datetime.datetime.now().replace(tzinfo=tz)

class OfferModelTest(TestCase):
  @classmethod
  def setUp(self):
    self.user_1 = User.objects.create_user(username='TestUser1')
    self.profile_1 = Profile.objects.create(user=self.user_1, f_name='TestFirstname1', l_name='TestLastname1')
    self.offer_1 = Offer.objects.create(
    owner=self.profile_1, 
    title='TestOffer1', 
    start_date=now - datetime.timedelta(hours=2), 
    end_date=now - datetime.timedelta(hours=1), 
    credit=1, 
    capacity=3, 
    app_deadline=now - datetime.timedelta(hours=12), 
    cancel_deadline=now - datetime.timedelta(hours=10), 
    offer_format='Offline', 
    offer_type='Service',
    description='TestOffer1'
    )
    self.offer_2 = Offer.objects.create(
    owner=self.profile_1, 
    title='TestOffer2', 
    start_date=now + datetime.timedelta(hours=7), 
    end_date=now + datetime.timedelta(hours=10), 
    credit=3, 
    capacity=3, 
    app_deadline=now + datetime.timedelta(hours=3), 
    cancel_deadline=now + datetime.timedelta(hours=5), 
    offer_format='Offline', 
    offer_type='Service',
    description='TestOffer2'
    )

    self.offer_3 = Offer.objects.create(
    owner=self.profile_1, 
    title='TestOffer3', 
    start_date=now + datetime.timedelta(hours=5), 
    end_date=now + datetime.timedelta(hours=7), 
    credit=0, 
    capacity=3, 
    app_deadline=now + datetime.timedelta(hours=1), 
    cancel_deadline=now + datetime.timedelta(hours=3), 
    offer_format='Offline', 
    offer_type='Event',
    description='TestOffer3',
    is_cancelled=True
    )
  
  def test_expiration_property_expired(self):
    """is_expired property of Offer"""
    self.assertEqual(self.offer_1.is_expired, True)

  def test_started_property_started(self):
    """is_started property of Offer"""
    self.assertEqual(self.offer_1.is_started, True)

  def test_apply_property_cannot_apply(self):
    """can_apply property of Offer"""
    self.assertEqual(self.offer_1.can_apply, False)

  def test_cancel_property_cannot_cancel(self):
    """can_cancel property of Offer"""
    self.assertEqual(self.offer_1.can_cancel, False)

  def test_expiration_property_not_expired(self):
    """is_expired property of Offer"""
    self.assertEqual(self.offer_2.is_expired, False)

  def test_started_property_not_started(self):
    """is_started property of Offer"""
    self.assertEqual(self.offer_2.is_started, False)

  def test_apply_property_can_apply(self):
    """can_apply property of Offer"""
    self.assertEqual(self.offer_2.can_apply, True)

  def test_cancel_property_can_cancel(self):
    """can_cancel property of Offer"""
    self.assertEqual(self.offer_2.can_cancel, True)

  def test_apply_property_cannot_apply_offer_cancelled(self):
    self.assertEqual(self.offer_3.can_apply, False)

class OfferModelFormTest(TestCase):
  def test_offer_model_form(self):
    form_data = {
    'title': 'TestTitle',
    'start_date': now + datetime.timedelta(hours=3), 
    'end_date': now + datetime.timedelta(hours=4), 
    'app_deadline': now + datetime.timedelta(hours=1), 
    'cancel_deadline': now + datetime.timedelta(hours=2), 
    'capacity': 2,
    'offer_format': 'Online', 
    'offer_type': 'Service',
    'description': 'TestDescription'
    }
    form = OfferModelForm(data=form_data)
    self.assertTrue(form.is_valid())

  def test_offer_model_form_invalid_title(self):
    form_data = {
    'title': 'T',
    'start_date': now + datetime.timedelta(hours=3), 
    'end_date': now + datetime.timedelta(hours=4), 
    'app_deadline': now + datetime.timedelta(hours=1), 
    'cancel_deadline': now + datetime.timedelta(hours=2), 
    'capacity': 2,
    'offer_format': 'Online', 
    'offer_type': 'Service',
    'description': 'TestDescription'
    }
    form = OfferModelForm(data=form_data)
    self.assertFalse(form.is_valid())

  def test_offer_model_form_invalid_end_date(self):
    form_data = {
    'title': 'TestTitle',
    'start_date': now + datetime.timedelta(hours=4), 
    'end_date': now + datetime.timedelta(hours=3), 
    'app_deadline': now + datetime.timedelta(hours=1), 
    'cancel_deadline': now + datetime.timedelta(hours=2), 
    'capacity': 2,
    'offer_format': 'Online', 
    'offer_type': 'Service',
    'description': 'TestDescription'
    }
    form = OfferModelForm(data=form_data)
    self.assertFalse(form.is_valid())

  def test_offer_model_form_invalid_app_deadline(self):
    form_data = {
    'title': 'TestTitle',
    'start_date': now + datetime.timedelta(hours=3), 
    'end_date': now + datetime.timedelta(hours=4), 
    'app_deadline': now + datetime.timedelta(hours=3), 
    'cancel_deadline': now + datetime.timedelta(hours=2), 
    'capacity': 2,
    'offer_format': 'Online', 
    'offer_type': 'Service',
    'description': 'TestDescription'
    }
    form = OfferModelForm(data=form_data)
    self.assertFalse(form.is_valid())

  def test_offer_model_form_invalid_cancel_deadline_start_date_fail(self):
    form_data = {
    'title': 'TestTitle',
    'start_date': now + datetime.timedelta(hours=3), 
    'end_date': now + datetime.timedelta(hours=4), 
    'app_deadline': now + datetime.timedelta(hours=2), 
    'cancel_deadline': now + datetime.timedelta(hours=3.1), 
    'capacity': 2,
    'offer_format': 'Online', 
    'offer_type': 'Service',
    'description': 'TestDescription'
    }
    form = OfferModelForm(data=form_data)
    self.assertFalse(form.is_valid())

  def test_offer_model_form_invalid_cancel_deadline_app_deadline_fail(self):
    form_data = {
    'title': 'TestTitle',
    'start_date': now + datetime.timedelta(hours=3), 
    'end_date': now + datetime.timedelta(hours=4), 
    'app_deadline': now + datetime.timedelta(hours=2.1), 
    'cancel_deadline': now + datetime.timedelta(hours=2), 
    'capacity': 2,
    'offer_format': 'Online', 
    'offer_type': 'Service',
    'description': 'TestDescription'
    }
    form = OfferModelForm(data=form_data)
    self.assertFalse(form.is_valid())

  def test_offer_model_form_invalid_capacity(self):
    form_data = {
    'title': 'TestTitle',
    'start_date': now + datetime.timedelta(hours=3), 
    'end_date': now + datetime.timedelta(hours=4), 
    'app_deadline': now + datetime.timedelta(hours=1), 
    'cancel_deadline': now + datetime.timedelta(hours=2), 
    'capacity': 0,
    'offer_format': 'Online', 
    'offer_type': 'Service',
    'description': 'TestDescription'
    }
    form = OfferModelForm(data=form_data)
    self.assertFalse(form.is_valid())

class TestOfferViews(TestCase):
  @classmethod
  def setUp(self):
    self.user_1 = User.objects.create_user(username='TestUser1', password='Test')
    self.profile_1 = Profile.objects.create(user=self.user_1, f_name='TestFirstname1', l_name='TestLastname1')
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
    self.client = Client()
  
  def test_offer_outlook_view(self):
    login = self.client.login(username='TestUser1', password='Test')
    response = self.client.get(reverse('offer_look', kwargs={'pk': self.offer_1.id}))
    self.assertEqual(response.status_code, 200)
    self.assertTemplateUsed(response, 'offers/outlook.html')

  def test_offer_create_view_saves_valid_object(self):
    login = self.client.login(username='TestUser1', password='Test')
    response = self.client.get(reverse('offer_create'))
    self.assertEqual(response.status_code, 200)
    self.assertTemplateUsed(response, 'offers/forms.html')
    data = {
    'image': '',
    'location': '',
    'title': 'TestTitle',
    'start_date': now + datetime.timedelta(hours=3), 
    'end_date': now + datetime.timedelta(hours=4), 
    'app_deadline': now + datetime.timedelta(hours=1), 
    'cancel_deadline': now + datetime.timedelta(hours=2), 
    'capacity': 2,
    'offer_format': 'Online', 
    'offer_type': 'Service',
    'description': 'TestDescription'
    }
    response = self.client.post(reverse('offer_create'), data)
    self.assertTrue(Offer.objects.get(title='TestTitle'))
    self.assertRedirects(response, reverse('offer_look', kwargs={'pk': Offer.objects.get(title='TestTitle').id}))

  def test_cancel_offer_view(self):
    login = self.client.login(username='TestUser1', password='Test')
    response = self.client.get(reverse('cancel_offer', kwargs={'offerID': self.offer_1.id}))
    self.assertRedirects(response, reverse('offer_look', kwargs={'pk': self.offer_1.id}))
  
  def tearDown(self):
    return super().tearDown()
