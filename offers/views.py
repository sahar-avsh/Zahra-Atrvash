from django.core.exceptions import ValidationError
from django.http.response import HttpResponse, JsonResponse, Http404, HttpResponseRedirect
from django.shortcuts import render, redirect
from django.urls import reverse
from django.contrib import messages

from categorytags.forms import OfferTagForm
from categorytags.models import OfferTag

from .models import Offer
from .forms import OfferModelForm
from profiles.models import Profile, ProfileJoinOfferRequest, ProfileReview
from profiles.views import convert_to_address

# Create your views here.
def offer_outlook_view(request, pk, *args, **kwargs):
  try:
    obj = Offer.objects.get(pk=pk)
    tag_list = obj.tags.all()
    obj_participants = obj.participants.all()
    num_of_spots_left = obj.capacity - obj_participants.count()
    address = convert_to_address(obj.loc_ltd, obj.loc_long)
    obj.update_status()
  except (Offer.DoesNotExist, ValidationError):
    raise Http404

  try:
    is_reviewed = ProfileReview.objects.get(review_giver=request.user.profile, offer=pk)
  except ProfileReview.DoesNotExist:
    is_reviewed = None

  try:
    join_offer_request = ProfileJoinOfferRequest.objects.get(profile=request.user.profile, offer=obj)
  except ProfileJoinOfferRequest.DoesNotExist:
    join_offer_request = None

  content = {'object': obj, 'join_request': join_offer_request, 'participants': obj_participants, 'spots_left': num_of_spots_left, 'is_reviewed': is_reviewed, 'tag_list': tag_list, 'address': address}
  return render(request, "offers/outlook.html", content)

def offer_create_view(request, *args, **kwargs):
  if request.method == 'POST':
    form = OfferModelForm(request.POST, request.FILES)
    form_offertag = OfferTagForm(request.POST)

    if form.is_valid():
      o = form.save(commit=False)
      o.owner = Profile.objects.get(user_id=request.user.id)
      end = form.cleaned_data['end_date']
      start = form.cleaned_data['start_date']
      offer_type = form.cleaned_data['offer_type']
      if offer_type == 'Service':
        o.credit = ((end - start).seconds) / 3600
      else:
        o.credit = 0

      loc = form.cleaned_data['location']
      loc_elements = loc.split(',')
      o.loc_long = loc_elements[0]
      o.loc_ltd = loc_elements[1]
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

def cancel_offer_view(request, offerID, *args, **kwargs):
  offer = Offer.objects.get(pk=offerID)
  offer.offer_status = 'Cancelled'
  offer.save()
  # remove all participants
  offer.participants.clear()
  # delete all join requests
  ProfileJoinOfferRequest.objects.filter(offer=offer).delete()
  return redirect('offer_look', pk=offerID)