from django.contrib import admin

from profiles.models import Profile, ProfileFollowRequest, ProfileJoinOfferRequest, ProfileReview

# Register your models here.
admin.site.register([Profile, ProfileFollowRequest, ProfileReview, ProfileJoinOfferRequest])
