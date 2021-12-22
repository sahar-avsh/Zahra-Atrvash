from django.db import models
import uuid

from django.db.models.deletion import CASCADE

from profiles.models import Profile
from offers.models import Offer

# Create your models here.
class Category(models.Model):
  id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
  name = models.CharField(max_length=100)

  def __str__(self) -> str:
      return self.name

class Skill(models.Model):
  user = models.ForeignKey(Profile, on_delete=CASCADE)
  cat = models.ForeignKey(Category, on_delete=CASCADE)
  # category = models.CharField(max_length=50, default="")

  # class Meta:
  #   constraints = [
  #   models.UniqueConstraint(fields=['user', 'category'], name='skill unique constraint')
  #   ]

  def __str__(self) -> str:
    return self.cat.name

class Interest(models.Model):
  user = models.ForeignKey(Profile, on_delete=CASCADE)
  cat = models.ForeignKey(Category, on_delete=CASCADE)
  # category = models.CharField(max_length=50, default="")

  # class Meta:
  #   constraints = [
  #   models.UniqueConstraint(fields=['user', 'category'], name='interest unique constraint')
  #   ]

  def __str__(self) -> str:
    return self.cat.name

class OfferCategory(models.Model):
  offer = models.ForeignKey(Offer, on_delete=CASCADE)
  cat = models.ForeignKey(Category, on_delete=CASCADE)
  # category = models.CharField(max_length=50, default="")

  # class Meta:
  #   constraints = [
  #   models.UniqueConstraint(fields=['offer', 'category'], name='offer unique constraint')
  #   ]
