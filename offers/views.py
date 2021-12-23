from django.core.exceptions import ValidationError
from django.http.response import HttpResponse, JsonResponse, Http404, HttpResponseRedirect
from django.shortcuts import render, redirect
from django.urls import reverse

from .models import Offer
from .forms import OfferModelForm
from profiles.models import Profile

# Create your views here.
def offer_outlook_view(request, pk, *args, **kwargs):
  try:
    obj = Offer.objects.get(pk=pk)
  except (Offer.DoesNotExist, ValidationError):
    raise Http404
  return render(request, "offers/outlook.html", {"object": obj})

def offer_create_view(request, *args, **kwargs):
  if request.method == 'POST':
    form = OfferModelForm(request.POST or None)
    if form != None:
      if form.is_valid():
        o = form.save(commit=False)
        o.owner = Profile.objects.get(user_id=request.user.id)
        # data = form.cleaned_data
        # o = Offer.objects.create(**data)
        return HttpResponseRedirect(reverse('offer_look', pk=o.id))
  else:
    form = OfferModelForm()
  return render(request, 'offers/forms.html', {'form': form})