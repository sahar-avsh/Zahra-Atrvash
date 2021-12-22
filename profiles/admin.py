from django.contrib import admin

from profiles.models import Profile, ProfileFollowing, ProfileReview

# Register your models here.
admin.site.register([Profile, ProfileFollowing, ProfileReview])
