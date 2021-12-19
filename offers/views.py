from django.core.exceptions import ValidationError
from django.http.response import HttpResponse, JsonResponse, Http404, HttpResponseRedirect
from django.shortcuts import render, redirect

from .models import Offer

# Create your views here.
def offer_outlook_view(request, pk, *args, **kwargs):
  try:
    obj = Offer.objects.get(pk=pk)
  except (Offer.DoesNotExist, ValidationError):
    raise Http404
  return render(request, "offers/outlook.html", {"object": obj})