from django.db import models
from django.db.models.deletion import CASCADE

from offers.models import Offer
from profiles.models import Profile

# Create your models here.
class Participant(models.Model):
  offer = models.ForeignKey(Offer, on_delete=CASCADE)
  participant = models.ForeignKey(Profile, on_delete=CASCADE)
  signed_at = models.DateTimeField(auto_now_add=True)
