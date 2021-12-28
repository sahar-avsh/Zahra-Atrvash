from django.db import models

# Create your models here.
class Skill(models.Model):
  skill_id = models.AutoField(primary_key=True)
  name = models.CharField(max_length=200, unique=True)

  def __str__(self) -> str:
      return self.name

class Interest(models.Model):
  interest_id = models.AutoField(primary_key=True)
  name = models.CharField(max_length=200, unique=True)

  def __str__(self) -> str:
    return self.name

class OfferTag(models.Model):
  offertag_id = models.AutoField(primary_key=True)
  name = models.CharField(max_length=200, unique=True)

  def __str__(self) -> str:
      return self.name
