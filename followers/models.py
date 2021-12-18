from django.db import models
from django.db.models.deletion import CASCADE

from profiles.models import Profile

# Create your models here.
class Follower(models.Model):
  follower = models.ForeignKey(Profile, on_delete=CASCADE, related_name='Follower+')
  following = models.ForeignKey(Profile, on_delete=CASCADE, related_name='Following+')
  followed_at = models.DateTimeField(auto_now_add=True)