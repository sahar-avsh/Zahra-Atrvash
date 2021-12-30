from django.db import models

from profiles.models import Profile

# Create your models here.
class ProfileMessage(models.Model):
  message_to = models.ForeignKey(Profile, related_name='receiver', on_delete=models.CASCADE)
  message_from = models.ForeignKey(Profile, related_name='sender', on_delete=models.CASCADE)
  title = models.TextField(null=True, blank=True)
  body = models.TextField()
  sent_at = models.DateTimeField(auto_now_add=True)

  def __str__(self) -> str:
      return self.message_from.f_name + '-->' + self.message_to.f_name