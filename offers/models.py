from django.db import models
from django.utils.translation import gettext_lazy as _
import uuid

from profiles.models import Profile

# Create your models here.
class Offer(models.Model):
  id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
  owner = models.ForeignKey(Profile, on_delete=models.CASCADE)
  title = models.CharField(max_length=220)
  image = models.ImageField(blank=True)
  loc_long = models.DecimalField(max_digits=9, decimal_places=6)
  loc_ltd = models.DecimalField(max_digits=9, decimal_places=6)
  created_at = models.DateTimeField(auto_now_add=True)
  start_date = models.DateTimeField()
  end_date = models.DateTimeField()
  capacity = models.IntegerField()
  app_deadline = models.DateTimeField()
  cancel_deadline = models.DateTimeField()

  class OfferFormat(models.TextChoices):
    online = 'ON', _('Online')
    offline = 'OF', _('Offline')

  offer_format = models.CharField(max_length=2, choices=OfferFormat.choices)

  class OfferType(models.TextChoices):
    event = 'EV', _('Event')
    service = 'SE', _('Service')

  offer_type = models.CharField(max_length=2, choices=OfferType.choices)

  description = models.TextField()