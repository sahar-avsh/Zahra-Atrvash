from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.db.models.signals import m2m_changed
from django.contrib.auth.models import User
import uuid

# Create your models here.
class Profile(models.Model):
  id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
  user = models.OneToOneField(User, on_delete=models.CASCADE)
  image = models.ImageField(blank=True, upload_to='images/')
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
  # offers that profile has requested to join
  outstanding_offers = models.ManyToManyField('offers.Offer', related_name='profiles_outstanding')
  # offers that profile has been accepted to join
  accepted_offers = models.ManyToManyField('offers.Offer', related_name='profiles_accepted')
  # skills that profile has
  skills = models.ManyToManyField('categorytags.Skill', related_name='profiles')
  # interests that profile has
  interests = models.ManyToManyField('categorytags.Interest', related_name='profiles')

  def __str__(self) -> str:
    return self.f_name + ' ' + self.l_name

class ProfileFollowing(models.Model):
  profile_id = models.ForeignKey('Profile', related_name='following', on_delete=models.CASCADE)
  following_profile_id = models.ForeignKey('Profile', related_name='followers', on_delete=models.CASCADE)
  created_at = models.DateTimeField(auto_now_add=True)

  def __str__(self) -> str:
      return self.profile_id.f_name + ' Follows ' + self.following_profile_id.f_name

class ProfileReview(models.Model):
  review_receiver_id = models.ForeignKey('Profile', related_name='review_giver', on_delete=models.CASCADE)
  review_giver_id = models.ForeignKey('Profile', related_name='review_receiver', on_delete=models.CASCADE)
  text = models.TextField()
  created_at = models.DateTimeField(auto_now_add=True)

  def __str__(self) -> str:
      return self.review_giver_id.f_name + '->' + self.review_receiver_id.f_name

