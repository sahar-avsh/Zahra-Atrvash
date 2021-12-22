from django.contrib import admin

from categorytags.models import Skill, Interest, OfferTag

# Register your models here.
admin.site.register([Skill, Interest, OfferTag])