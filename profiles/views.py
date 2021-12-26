from django.core.exceptions import ValidationError
from django.http.response import HttpResponse, JsonResponse, Http404, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.decorators import login_required
from django.urls import reverse

from allauth.account.signals import user_signed_up
from django.dispatch import receiver

from .forms import ProfileModelForm
from .models import Profile, ProfileFollowRequest, ProfileJoinOfferRequest
from offers.models import Offer
from categorytags.models import Skill, Interest

# Create your views here.
@receiver(user_signed_up)
def after_user_signed_up(request, user, **kwargs):
  profile = Profile.objects.create(user=user, f_name=user.first_name, l_name=user.last_name, email=user.email)

def home_view(request, *args, **kwargs):
  qs_offers = Offer.objects.all()
  # get the active user with request.user
  # get following list and list their joined offers
  content = {'offer_list': qs_offers}
  return render(request, 'home.html', content)

def profile_edit_view(request, *args, **kwargs):
  profile = get_object_or_404(Profile, pk=request.user.profile.id)
  if request.method == 'POST':
    form = ProfileModelForm(request.POST, request.FILES, instance=profile)
    if form.is_valid():
      profile = form.save()
      return redirect('profile_look', pk=profile.id)
    print(form.errors)
  else:
    form = ProfileModelForm(instance=profile)
  return render(request, "profiles/forms.html", {'form': form, 'object': profile})

def profile_outlook_view(request, pk, *args, **kwargs):
  current_profile = request.user.profile
  current_profile_friend_list = current_profile.friends.all()
  try:
    obj = Profile.objects.get(pk=pk)
    skill_list = obj.skills.all()
    interest_list = obj.interests.all()
    friend_list = obj.friends.all()
  except (Profile.DoesNotExist, ValidationError):
    raise Http404

  try:
    current_profile_friend_request = ProfileFollowRequest.objects.get(profile_id=current_profile, following_profile_id=obj)
  except:
    current_profile_friend_request = None

  return render(request, "profiles/outlook.html", {"object": obj, "user": current_profile,
   "skill_list": skill_list, "interest_list": interest_list, 'friend_list': friend_list, 
   'user_friend_list': current_profile_friend_list, 'user_friend_request': current_profile_friend_request})

def profile_notifications_view(request, *args, **kwargs):
  current_profile = request.user.profile
  offers_of_current_profile = Offer.objects.filter(owner=current_profile)
  try:
    friend_requests = ProfileFollowRequest.objects.all().filter(following_profile_id=current_profile)
    join_requests = ProfileJoinOfferRequest.objects.all().filter(offer__in=offers_of_current_profile)
  except ProfileFollowRequest.DoesNotExist:
    friend_requests = None
    join_requests = None
  content = {"friend_list": friend_requests, 'offer_list': join_requests}
  return render(request, "profiles/notifications.html", content)

def profile_activity_background_view(request, profileID, *args, **kwargs):
  obj = Profile.objects.get(pk=profileID)
  created_active_offers = Offer.objects.filter(owner=obj, offer_status='Active')
  cancelled_or_passive_offers = Offer.objects.filter(owner=obj, offer_status__in=['Cancelled', 'Passive'])
  joined_offers = obj.accepted_offers.all()
  outstanding_offer_requests = ProfileJoinOfferRequest.objects.filter(profile=obj)
  content = {'created_active_offers': created_active_offers,
  'cancelled_passive_offers': cancelled_or_passive_offers,
  'joined_offers': joined_offers,
  'outstanding_offers': outstanding_offer_requests, 'obj': obj}
  return render(request, "profiles/activity_background.html", content)

""" def profile_api_detail_view(request, pk, *args, **kwargs):
  try:
      obj = Profile.objects.get(pk=pk)
  except (Profile.DoesNotExist, ValidationError):
      return JsonResponse(
          {"Message": "Not found!"}, status=404
      )  # render JSON with HTTP status code of 404
  return JsonResponse({"First name": obj.f_name}) """

def send_follow_request(request, profileID):
  from_profile = request.user.profile
  to_profile = Profile.objects.get(pk=profileID)
  follow_request, created = ProfileFollowRequest.objects.get_or_create(
    profile_id=from_profile, following_profile_id=to_profile
  )
  if created:
    return redirect('home_page')
  else:
    return redirect('home_page')

def unfollow(request, profileID):
    from_profile = request.user.profile
    to_profile = Profile.objects.get(pk=profileID)
    from_profile.friends.remove(to_profile)
    to_profile.friends.remove(from_profile)
    return redirect('home_page')

def accept_follow_request(request, follow_request_id):
  follow_request = ProfileFollowRequest.objects.get(id=follow_request_id)
  if follow_request.following_profile_id == request.user.profile:
    follow_request.profile_id.friends.add(follow_request.following_profile_id)
    follow_request.following_profile_id.friends.add(follow_request.profile_id)
    follow_request.delete()
    return redirect('home_page')
  else:
    return redirect('home_page')

def decline_follow_request(request, follow_request_id):
  follow_request = ProfileFollowRequest.objects.get(id=follow_request_id)
  if follow_request.following_profile_id == request.user.profile:
    follow_request.delete()
    return redirect('home_page')
  else:
    return redirect('home_page')

def cancel_follow_request(request, follow_request_id):
  follow_request = ProfileFollowRequest.objects.get(id=follow_request_id)
  if follow_request.profile_id == request.user.profile:
    follow_request.delete()
    return redirect('home_page')
  else:
    return redirect('home_page')

def profile_friends_view(request, profileID, *args, **kwargs):
  # current_profile = request.user.profile
  obj = Profile.objects.get(pk=profileID)
  friend_list = obj.friends.all()
  content = {"object": obj, "object_list": friend_list}
  return render(request, "profiles/friends.html", content)

def send_join_request(request, offerID, *args, **kwargs):
  from_profile = request.user.profile
  to_offer = Offer.objects.get(pk=offerID)

  # check if profile has enough credits to join this offer
  available_credits = from_profile.credit
  required_credits = to_offer.credit
  # also check if offer has enough capacity
  num_of_participants = to_offer.participants.count()

  if available_credits >= required_credits and num_of_participants < to_offer.capacity:
    join_request, created = ProfileJoinOfferRequest.objects.get_or_create(
    profile=from_profile, offer=to_offer
  )
    if created:
      return redirect('home_page')
    else:
      return redirect('home_page')
  else:
    return redirect('home_page')

def accept_join_request(request, join_request_id):
  join_request = ProfileJoinOfferRequest.objects.get(id=join_request_id)
  if join_request.offer.owner == request.user.profile:
    # add profile to offer's participants
    join_request.offer.participants.add(join_request.profile)
    # add offer to profile's accepted offers
    join_request.profile.accepted_offers.add(join_request.offer)
    # deduct credits from the participant
    if join_request.profile.credit < join_request.offer.credit:
      Profile.objects.filter(pk=join_request.profile.id).update(credit=0.00)
    else:
      remaining_credits = join_request.profile.credit - join_request.offer.credit
      Profile.objects.filter(pk=join_request.profile.id).update(credit=remaining_credits)
    join_request.delete()
    return redirect('home_page')
  else:
    return redirect('home_page')

def decline_join_request(request, join_request_id):
  join_request = ProfileJoinOfferRequest.objects.get(id=join_request_id)
  if join_request.offer.owner == request.user.profile:
    join_request.delete()
    return redirect('home_page')
  else:
    return redirect('home_page')

def cancel_join_request(request, join_request_id):
  join_request = ProfileJoinOfferRequest.objects.get(id=join_request_id)
  if join_request.profile == request.user.profile:
    join_request.delete()
  return redirect('home_page')

def leave_offer(request, offerID):
  offer = Offer.objects.get(pk=offerID)
  if request.user.profile in offer.participants.all():
    # give profile's credits back
    offer_creds = offer.credit
    profile_creds = request.user.profile.credit
    Profile.objects.filter(pk=request.user.profile.id).update(credit=offer_creds + profile_creds)
    # remove profile from offer participants
    offer.participants.remove(request.user.profile)
    # remove the offer from profile's accepted offers
    request.user.profile.accepted_offers.remove(offer)
    return redirect('home_page')