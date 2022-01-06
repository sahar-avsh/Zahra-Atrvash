from django.core.exceptions import BadRequest, ValidationError
from django.http.response import HttpResponse, JsonResponse, Http404, HttpResponseRedirect
from django.shortcuts import render, redirect
from django.urls import reverse
from django.contrib import messages
from django.contrib.auth.decorators import login_required

from django.db.models import F
from django.contrib.gis.db.models.functions import Distance
from django.contrib.gis.measure import D
from django.contrib.gis.measure import Distance as Dist
from django.contrib.gis.geos import Point

from categorytags.forms import OfferTagForm
from categorytags.models import OfferTag

from .models import Offer
from .forms import OfferFilterForm, OfferModelForm
from profiles.models import OwnerToParticipantReview, Profile, ProfileJoinOfferRequest, ProfileReview
from profiles.views import convert_to_address, retract_participant_credit

from django.db.models import Q, query
import pytz
import datetime
from geopy.distance import great_circle
import math
from decimal import Decimal

# Create your views here.



#******************** Offer outlook page ********************
@login_required
def offer_outlook_view(request, pk, *args, **kwargs):
  try:
    # get offer object
    obj = Offer.objects.get(pk=pk)
    # get tags - For everyone
    tag_list = obj.tags.all()
    # get participants - For owner
    obj_participants = obj.participants.all()
    # get number of spots left - For everyone
    num_of_spots_left = obj.capacity - obj_participants.count()
    # get address - For everyone
    address = convert_to_address(obj.loc_ltd, obj.loc_long)

    # check for each participant if they reviewed the offer and marked it as approved
    participant_approvals = {}
    for i in obj_participants:
      try:
        p = ProfileReview.objects.get(review_giver=i, offer=obj)
        review = p.done
      except ProfileReview.DoesNotExist:
        review = None
      participant_approvals[i] = review

    # check if offer owner approved
    owner_approval = obj.approval_status

    # check if offer owner rated the participants
    owner_to_participant_rates = {}
    for i in obj_participants:
      try:
        r = OwnerToParticipantReview.objects.get(offer=obj, participant=i)
      except OwnerToParticipantReview.DoesNotExist:
        r = None
      owner_to_participant_rates[i] = r

  except (Offer.DoesNotExist, ValidationError):
    raise Http404

  try:
    is_reviewed = ProfileReview.objects.get(review_giver=request.user.profile, offer=obj)
  except ProfileReview.DoesNotExist:
    is_reviewed = None

  try:
    join_offer_request = ProfileJoinOfferRequest.objects.get(profile=request.user.profile, offer=obj, is_accepted=None)
  except ProfileJoinOfferRequest.DoesNotExist:
    join_offer_request = None

  content = {'object': obj, 'join_request': join_offer_request, 'participants': obj_participants,
  'spots_left': num_of_spots_left, 'is_reviewed': is_reviewed, 'tag_list': tag_list,
  'address': address, 'participant_approvals': participant_approvals, 'owner_approval': owner_approval,
  'owner_to_participant': owner_to_participant_rates}
  return render(request, "offers/outlook.html", content)



#******************** Offer creation page  ********************
@login_required
def offer_create_view(request, *args, **kwargs):
  if request.method == 'POST':
    form = OfferModelForm(request.POST, request.FILES)
    form_offertag = OfferTagForm(request.POST)

    if form.is_valid():
      o = form.save(commit=False)
      end = form.cleaned_data['end_date']
      start = form.cleaned_data['start_date']

      intersecting_offers = Offer.objects.filter(Q(owner=request.user.profile) & (Q(start_date__gte=start) & Q(end_date__lte=end)))
      if intersecting_offers:
        messages.error(request, 'You have conflicting offers at the same time slot.')
      else:
        o.owner = Profile.objects.get(user_id=request.user.id)
        offer_type = form.cleaned_data['offer_type']
        if offer_type == 'Service':
          o.credit = Decimal(((end - start).seconds) / 3600)
        else:
          o.credit = Decimal(0)

        # if the provider capped credits, cannot create an offer
        num_of_participants = form.cleaned_data['capacity']
        if o.credit * num_of_participants + request.user.profile.credit > 15 :
          messages.error(request, 'You have capped your credits (15). Either lower capacity or credit requirement.')
        else:

          loc = form.cleaned_data['location']
          loc_elements = loc.split(',')
          o.loc_long = loc_elements[0]
          o.loc_ltd = loc_elements[1]
          o.location = Point(float(o.loc_long), float(o.loc_ltd))
          o.save()

          if form_offertag.is_valid():
            entry = [word.strip() for word in form_offertag.cleaned_data['offer_tag_name'].split(',') if word.strip() != '']

            for i in entry:
              obj, created = OfferTag.objects.get_or_create(name=i.title())
              if obj not in o.tags.all():
                o.tags.add(obj)

            messages.success(request, 'Your offer is created successfully.')
            return redirect('offer_look', pk=o.id)
  else:
    form = OfferModelForm()
    form_offertag = OfferTagForm()
  return render(request, 'offers/forms.html', {'form': form, 'form_offertag': form_offertag})


#******************** canceling an already created offer  ********************
@login_required
def cancel_offer_view(request, offerID, *args, **kwargs):
  offer = Offer.objects.get(pk=offerID)
  offer.offer_status = 'Cancelled'
  offer.save()

  # give all participants their credits back
  participants = offer.participants.all()
  for p in participants:
    retract_participant_credit(p.id, offer.id)
  # give profiles who had a join request their credits back
  join_requests = ProfileJoinOfferRequest.objects.filter(offer=offer)
  for j in join_requests:
    retract_participant_credit(j.profile.id, offer.id)

  # remove all participants
  offer.participants.clear()
  # delete all join requests
  ProfileJoinOfferRequest.objects.filter(offer=offer).delete()
  return redirect('offer_look', pk=offerID)


#******************** Timeline page  ********************
@login_required
def timeline_view(request, *args, **kwargs):
  try:
    current_location = Point(float(request.user.profile.loc_ltd), float(request.user.profile.loc_long), srid=4326)
  except TypeError:
    current_location = None

  utc = pytz.UTC
  now = datetime.datetime.now().replace(tzinfo=utc)

  if request.method == 'POST':
    form = OfferFilterForm(request.POST)
    empty_flag = False
    if form.is_valid():
      if current_location:
        qs = Offer.objects.filter(is_cancelled=False, app_deadline__gt=now).annotate(distance=Distance('location', current_location))
      for key, value in form.cleaned_data.items():
        if key == 'distance' and value:
          max_distance = value # distance in meter
          d = distance_to_decimal_degrees(Dist(m=max_distance), float(request.user.profile.loc_long))
          qs = qs.annotate(distance=Distance('location', current_location)).filter(distance__lte=d)
        if key == 'credit' and value:
          qs = qs.filter(credit__lte=value)
        if key == 'title' and value:
          qs = qs.filter(Q(title__icontains=value) | Q(description__icontains=value))
        if key == 'start_date' and value:
          qs = qs.filter(start_date__date__gte=value)
        if key == 'tags' and value != '':
          entry = [word.strip().title() for word in value.split(',') if word.strip() != '']
          qs = qs.filter(tags__name__in=entry)
        if key == 'offer_type' and value:
          if value == 'All':
            pass
          else:
            qs = qs.filter(offer_type=value)
      if current_location:
        qs = qs.order_by('distance')
      qs_dist = {}
      for o in qs:
        qs_dist[o] = round(great_circle(o.location, current_location).km, 2)
      
      qs = qs.exclude(owner=request.user.profile)

      content = {
        'form': form,
        'qs': qs,
        'qs_dist': qs_dist,
        'flag': empty_flag,
        'current_location': current_location,
      }
      return render(request, 'offers/timeline_view.html', content)
  else:
    form = OfferFilterForm()
    empty_flag = True
    if current_location:
      qs = Offer.objects.filter(is_cancelled=False, app_deadline__gt=now).annotate(distance=Distance('location', current_location)).order_by('distance')
    else:
      qs = Offer.objects.filter(is_cancelled=False, app_deadline__gt=now).order_by('start_date')

    qs_dist = {}
    for o in qs:
      qs_dist[o] = round(great_circle(o.location, current_location).km, 2)

    qs = qs.exclude(owner=request.user.profile)

    content = {
      'form': form,
      'qs': qs,
      'qs_dist': qs_dist,
      'flag': empty_flag,
      'current_location': current_location,
    }
  return render(request, 'offers/timeline_view.html', content)



#******************** Changing degree to km functionality  ********************
def distance_to_decimal_degrees(distance, latitude):
  """
  Source of formulae information:
      1. https://en.wikipedia.org/wiki/Decimal_degrees
      2. http://www.movable-type.co.uk/scripts/latlong.html
  :param distance: an instance of `from django.contrib.gis.measure.Distance`
  :param latitude: y - coordinate of a point/location
  """
  lat_radians = latitude * (math.pi / 180)
  # 1 longitudinal degree at the equator equal 111,319.5m equiv to 111.32km
  return distance.m / (111_319.5 * math.cos(lat_radians))