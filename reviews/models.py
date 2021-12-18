from django.db import models

from profiles.models import Profile
from offers.models import Offer

# Create your models here.
class Review(models.Model):
  user = models.ForeignKey(Profile, on_delete=models.CASCADE)
  offer = models.ForeignKey(Offer, on_delete=models.CASCADE)
  rate = models.PositiveSmallIntegerField(blank=True)
  review = models.TextField(blank=True)
  created_at = models.DateTimeField(auto_now_add=True)
