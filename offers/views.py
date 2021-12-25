from django.core.exceptions import ValidationError
from django.http.response import HttpResponse, JsonResponse, Http404, HttpResponseRedirect
from django.shortcuts import render, redirect
from django.urls import reverse

from .models import Offer
from .forms import OfferModelForm
from profiles.models import Profile, ProfileJoinOfferRequest

# Create your views here.
def offer_outlook_view(request, pk, *args, **kwargs):
  try:
    obj = Offer.objects.get(pk=pk)
    obj_participants = obj.participants.all()
    num_of_spots_left = obj.capacity - obj_participants.count()
  except (Offer.DoesNotExist, ValidationError):
    raise Http404

  try:
    join_offer_request = ProfileJoinOfferRequest.objects.get(profile=request.user.profile, offer=obj)
  except ProfileJoinOfferRequest.DoesNotExist:
    join_offer_request = None

  content = {'object': obj, 'join_request': join_offer_request, 'participants': obj_participants, 'spots_left': num_of_spots_left}
  return render(request, "offers/outlook.html", content)

def offer_create_view(request, *args, **kwargs):
  if request.method == 'POST':
    form = OfferModelForm(request.POST, request.FILES or None)
    if form != None:
      if form.is_valid():
        o = form.save(commit=False)
        o.owner = Profile.objects.get(user_id=request.user.id)
        end = form.cleaned_data['end_date']
        start = form.cleaned_data['start_date']
        o.credit = ((end - start).seconds) / 3600
        o.save()
        o.tags.set(form.cleaned_data['tags'])
        # data = form.cleaned_data
        # o = Offer.objects.create(**data)
        return HttpResponseRedirect(reverse('offer_look', kwargs={'pk': o.id}))
  else:
    form = OfferModelForm()
  return render(request, 'offers/forms.html', {'form': form})

def cancel_offer_view(request, offerID, *args, **kwargs):
  offer = Offer.objects.get(pk=offerID)
  offer.offer_status = 'Cancelled'
  offer.save()
  # remove all participants
  offer.participants.clear()
  # delete all join requests
  ProfileJoinOfferRequest.objects.filter(offer=offer).delete()
  return redirect('offer_look', pk=offerID)