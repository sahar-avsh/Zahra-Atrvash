from django.contrib import admin
# from mapbox_location_field.admin import MapAdmin

from profiles.models import OwnerToParticipantReview, Profile, ProfileFollowRequest, ProfileJoinOfferRequest, ProfileReview

# Register your models here.
admin.site.register([Profile, ProfileFollowRequest, ProfileReview, ProfileJoinOfferRequest, OwnerToParticipantReview])
