from django.db import models
from django.utils.translation import gettext_lazy as _
import uuid

# Create your models here.
class Profile(models.Model):
  id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
  image = models.ImageField(blank=True)
  f_name = models.CharField(max_length=50)
  l_name = models.CharField(max_length=50)
  created_at = models.DateTimeField(auto_now_add=True)
  email = models.EmailField()
  birthday = models.DateField()
  occupation = models.CharField(blank=True, max_length=50)

  loc_long = models.DecimalField(max_digits=9, decimal_places=6, blank=True)
  loc_ltd = models.DecimalField(max_digits=9, decimal_places=6, blank=True)

  class DiplomaReceived(models.TextChoices):
    other = 'Other', _('Other')
    high_school = 'High School Diploma', _('High School Diploma')
    associate = 'Associate Degree', _('Associate Degree')
    undergraduate = 'Undergraduate Degree', _('Undergraduate Degree')
    postgraduate = 'Postgradute Degree', _('Postgraduate Degree')

  education = models.CharField(max_length=50, choices=DiplomaReceived.choices, blank=True)

  description = models.TextField(blank=True)
  credit = models.IntegerField(default=0)
