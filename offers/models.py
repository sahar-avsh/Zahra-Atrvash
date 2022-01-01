from django.db import models
from django.utils.translation import gettext_lazy as _
import uuid
import datetime
import pytz
from geopy.distance import great_circle
from django.contrib.gis.db import models as gis_models

from profiles.models import Profile

# Create your models here.
class Offer(models.Model):
  id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
  owner = models.ForeignKey(Profile, on_delete=models.CASCADE)
  title = models.CharField(max_length=220)
  image = models.ImageField(blank=True, upload_to='images/')

  loc_long = models.DecimalField(max_digits=9, decimal_places=6)
  loc_ltd = models.DecimalField(max_digits=9, decimal_places=6)
  location = gis_models.PointField(null=True, blank=True, srid=4326, verbose_name='Location')

  created_at = models.DateTimeField(auto_now_add=True)
  start_date = models.DateTimeField()
  end_date = models.DateTimeField()
  credit = models.DecimalField(max_digits=4, decimal_places=2, default=0)
  capacity = models.IntegerField()
  app_deadline = models.DateTimeField()
  cancel_deadline = models.DateTimeField()

  class OfferFormat(models.TextChoices):
    online = 'Online', _('Online')
    offline = 'Offline', _('Offline')

  offer_format = models.CharField(max_length=7, choices=OfferFormat.choices)

  class OfferType(models.TextChoices):
    event = 'Event', _('Event')
    service = 'Service', _('Service')

  offer_type = models.CharField(max_length=7, choices=OfferType.choices)

  class OfferStatus(models.TextChoices):
    # offer is active and not given yet
    active = 'Active', _('Active')
    # offer is given
    passive = 'Passive', _('Passive')
    # offer is cancelled
    cancelled = 'Cancelled', _('Cancelled')

  offer_status = models.CharField(max_length=10, choices=OfferStatus.choices, default='Active')

  class ApprovalStatus(models.TextChoices):
    # approved
    approve = 'Approved', _('Approved')
    # not approved
    decline = 'Declined', _('Declined')
    # outstanding
    outstanding = 'Outstanding', _('Outstanding')

  approval_status = models.CharField(max_length=11, choices=ApprovalStatus.choices, default='Outstanding')

  description = models.TextField()
  # category tags that an offer has
  tags = models.ManyToManyField('categorytags.OfferTag', related_name='offers', blank=True)
  # participants
  participants = models.ManyToManyField('profiles.Profile', related_name='offer_participants', blank=True)

  def update_status(self):
    utc = pytz.UTC
    now = datetime.datetime.now().replace(tzinfo=utc)
    # here we check if the offer end date has passed
    if self.end_date <= now:
      Offer.objects.filter(id=self.id, offer_status='Active').update(offer_status='Passive')
      return True
    else:
      return False

  def __str__(self) -> str:
      return self.owner.f_name + '-' + self.title