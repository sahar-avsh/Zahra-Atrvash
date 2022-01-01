from django.core.exceptions import ValidationError
from django.http.response import HttpResponse, JsonResponse, Http404, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.contrib import messages

from allauth.account.signals import user_signed_up, user_logged_in
from django.dispatch import receiver

from categorytags.forms import InterestForm, SkillForm
from offers.forms import ApproveForm

from .forms import OwnerToParticipantReviewForm, ProfileModelForm, ReviewForm
from .models import Profile, ProfileFollowRequest, ProfileJoinOfferRequest, ProfileReview, OwnerToParticipantReview
from offers.models import Offer
from categorytags.models import Skill, Interest

from django.db.models import Q
import pytz
import datetime
from geopy.distance import great_circle

# Create your views here.
@receiver(user_signed_up)
def after_user_signed_up(user, **kwargs):
  profile = Profile.objects.create(user=user, f_name=user.first_name, l_name=user.last_name, email=user.email)

@receiver(user_logged_in)
def after_user_signed_in(user, **kwargs):
  qs_offers = Offer.objects.all()
  for i in qs_offers:
    u = i.update_status()
    r1 = automatic_offer_approval(i.id)
    r2 = automatic_offer_review(user.profile, i.id)

  qs_join_requests = ProfileJoinOfferRequest.objects.filter(profile=user.profile)
  for r in qs_join_requests:
    unanswered_join_request(r.id)

@login_required
def home_view(request, *args, **kwargs):
  return render(request, 'home.html')

@login_required
def profile_rate_reviews_view(request, profileID, *args, **kwargs):
  obj = Profile.objects.get(pk=profileID)
  passive_offers = Offer.objects.filter(owner=obj, offer_status='Passive')
  qs_reviews = ProfileReview.objects.filter(offer__in=passive_offers)
  qs_participant_reviews = OwnerToParticipantReview.objects.filter(participant=obj)
  no_of_reviews = qs_reviews.filter(~Q(rating=0)).count()
  no_of_participant_reviews = qs_participant_reviews.count()
  total_number_reviews = no_of_reviews + no_of_participant_reviews
  # calculate average rating over all offers and reviews
  if total_number_reviews > 0:
    total = 0
    for i in qs_reviews:
      total += i.rating
    for j in qs_participant_reviews:
      total += j.rating

    avg_rating = total / total_number_reviews

    # calc no of 5 star reviews
    five_stars = qs_reviews.filter(rating=5).count() + qs_participant_reviews.filter(rating=5).count()
    four_stars = qs_reviews.filter(rating=4).count() + qs_participant_reviews.filter(rating=4).count()
    three_stars = qs_reviews.filter(rating=3).count() + qs_participant_reviews.filter(rating=3).count()
    two_stars = qs_reviews.filter(rating=2).count() + qs_participant_reviews.filter(rating=2).count()
    one_stars = qs_reviews.filter(rating=1).count() + qs_participant_reviews.filter(rating=1).count()
  else:
    avg_rating = 0
    five_stars = 0
    four_stars = 0
    three_stars = 0
    two_stars = 0
    one_stars = 0

  return render(request, 'profiles/rates_reviews.html', {'object_list': qs_reviews, 
  'no_of_reviews': total_number_reviews, 'avg_rating': avg_rating, 'five_stars': five_stars, 'four_stars': four_stars,
  'three_stars': three_stars, 'two_stars': two_stars, 'one_stars': one_stars,
  'participant_reviews': qs_participant_reviews})

@login_required
def profile_edit_view(request, *args, **kwargs):
  profile = get_object_or_404(Profile, pk=request.user.profile.id)
  qs_skills = profile.skills.all()
  qs_interests = profile.interests.all()

  if request.method == 'POST':
    form = ProfileModelForm(request.POST, request.FILES, instance=profile)
    form_skill = SkillForm(request.POST)
    form_interest = InterestForm(request.POST)

    if form.is_valid():
      profile = form.save(commit=False)
      loc = form.cleaned_data['location']
      loc_elements = loc.split(',')
      profile.loc_long = loc_elements[0]
      profile.loc_ltd = loc_elements[1]
      profile.save()

    if form_skill.is_valid():
      entry_s = [word.strip() for word in form_skill.cleaned_data['skill_name'].split(',') if word.strip() != '']
      remove_s = [word.strip() for word in form_skill.cleaned_data['skill_name_remove'].split(',') if word.strip() != '']

      for i in entry_s:
        obj, created = Skill.objects.get_or_create(name=i.title())
        if obj not in qs_skills:
          profile.skills.add(obj)

      for t in remove_s:
        try:
          obj_s_remove = Skill.objects.get(name=t.title())
        except Skill.DoesNotExist:
          obj_s_remove = None
        if obj_s_remove != None and obj_s_remove in qs_skills:
          profile.skills.remove(obj_s_remove)

    if form_interest.is_valid():
      entry_i = [word.strip() for word in form_interest.cleaned_data['interest_name'].split(',') if word.strip() != '']
      remove_i = [word.strip() for word in form_interest.cleaned_data['interest_name_remove'].split(',') if word.strip() != '']

      for j in entry_i:
        obj_i, created = Interest.objects.get_or_create(name=j.title())
        if obj_i not in qs_interests:
          profile.interests.add(obj_i)

      for r in remove_i:
        try:
          obj_i_remove = Interest.objects.get(name=r.title())
        except Interest.DoesNotExist:
          obj_i_remove = None
        if obj_i_remove != None and obj_i_remove in qs_interests:
          profile.interests.remove(obj_i_remove)

    messages.success(request, 'Your profile is updated successfully.')
    return redirect('profile_look', pk=profile.id)
  else:
    form = ProfileModelForm(instance=profile)
    form_skill = SkillForm()
    form_interest = InterestForm()
  return render(request, "profiles/forms.html", 
  {'form': form, 'object': profile, 'skill_form': form_skill, 'interest_form': form_interest, 
  'object_skills': qs_skills, 'object_interests': qs_interests})

@login_required
def profile_outlook_view(request, pk, *args, **kwargs):
  current_profile = request.user.profile
  current_profile_friend_list = current_profile.friends.all()
  try:
    obj = Profile.objects.get(pk=pk)
    skill_list = obj.skills.all()
    interest_list = obj.interests.all()
    friend_list = obj.friends.all()
    if obj.loc_ltd != None and obj.loc_long != None:
      address_flag = True
      address = convert_to_address(obj.loc_ltd, obj.loc_long)
    else:
      address = None
      address_flag = False
  except (Profile.DoesNotExist, ValidationError):
    raise Http404

  try:
    current_profile_friend_request = ProfileFollowRequest.objects.get(profile_id=current_profile, following_profile_id=obj)
  except:
    current_profile_friend_request = None

  return render(request, "profiles/outlook.html", {"object": obj, "user": current_profile,
   "skill_list": skill_list, "interest_list": interest_list, 'friend_list': friend_list, 
   'user_friend_list': current_profile_friend_list, 'user_friend_request': current_profile_friend_request,
  'address_flag': address_flag, 'address': address})

def convert_to_address(lat, long):
  from geopy.geocoders import Nominatim
  from functools import partial
  geolocator = Nominatim(user_agent='profiles')
  reverse = partial(geolocator.reverse, language="en")
  coords = str(lat) + ', ' + str(long)
  location = reverse(coords)
  #address = location.raw['address']
  if location != None:
    address = location.address
  else:
    address = None
  return address

@login_required
def profile_notifications_view(request, *args, **kwargs):
  current_profile = request.user.profile
  offers_of_current_profile = Offer.objects.filter(owner=current_profile)

  offers_outstanding_approvals = Offer.objects.filter(owner=current_profile, offer_status='Passive', approval_status='Outstanding')

  finished_joined_offers = current_profile.accepted_offers.filter(offer_status='Passive')
  outstanding_offer_reviews = []
  for o in finished_joined_offers:
    try:
      review = ProfileReview.objects.get(review_giver=current_profile, offer=o)
    except ProfileReview.DoesNotExist:
      review = None
    if review == None:
      outstanding_offer_reviews.append(o)

  try:
    friend_requests = ProfileFollowRequest.objects.all().filter(following_profile_id=current_profile)
    join_requests = ProfileJoinOfferRequest.objects.all().filter(offer__in=offers_of_current_profile)

    # check if app deadline has passed for each offer from join request object
    utc = pytz.UTC
    now = datetime.datetime.now().replace(tzinfo=utc)
    join_request_dict = {}
    for j in join_requests:
      if now > j.offer.app_deadline:
        join_request_dict[j] = False
      else:
        join_request_dict[j] = True

    declined_join_requests = ProfileJoinOfferRequest.objects.filter(profile=current_profile, is_accepted=False)

  except (ProfileFollowRequest.DoesNotExist, ProfileJoinOfferRequest.DoesNotExist):
    friend_requests = None
    join_requests = None
    declined_join_requests = None


  content = {"friend_list": friend_requests, 'offer_list': join_requests,
   'outstanding_offer_reviews': outstanding_offer_reviews, 'len_outstanding_reviews': len(outstanding_offer_reviews),
  'outstanding_approvals': offers_outstanding_approvals, 'join_request_dict': join_request_dict, 'declined_join_requests': declined_join_requests}
  return render(request, "profiles/notifications.html", content)

@login_required
def profile_activity_background_view(request, profileID, *args, **kwargs):
  obj = Profile.objects.get(pk=profileID)
  created_active_offers = Offer.objects.filter(owner=obj, offer_status='Active')
  cancelled_or_passive_offers = Offer.objects.filter(owner=obj, offer_status__in=['Cancelled', 'Passive'])
  joined_offers = obj.accepted_offers.all()

  outstanding_offer_requests = ProfileJoinOfferRequest.objects.filter(profile=obj, is_accepted=False)
  # check if app deadline has passed for each offer from join request object
  utc = pytz.UTC
  now = datetime.datetime.now().replace(tzinfo=utc)
  join_request_dict = {}
  for j in outstanding_offer_requests:
    if now > j.offer.app_deadline:
      join_request_dict[j] = False
    else:
      join_request_dict[j] = True

  content = {'created_active_offers': created_active_offers,
  'cancelled_passive_offers': cancelled_or_passive_offers,
  'joined_offers': joined_offers,
  'outstanding_offers': outstanding_offer_requests, 'obj': obj, 'join_request_dict': join_request_dict}
  return render(request, "profiles/activity_background.html", content)

""" def profile_api_detail_view(request, pk, *args, **kwargs):
  try:
      obj = Profile.objects.get(pk=pk)
  except (Profile.DoesNotExist, ValidationError):
      return JsonResponse(
          {"Message": "Not found!"}, status=404
      )  # render JSON with HTTP status code of 404
  return JsonResponse({"First name": obj.f_name}) """

@login_required
def send_follow_request(request, profileID):
  from_profile = request.user.profile
  to_profile = Profile.objects.get(pk=profileID)
  follow_request, created = ProfileFollowRequest.objects.get_or_create(
    profile_id=from_profile, following_profile_id=to_profile
  )
  if created:
    messages.success(request, 'Your follow request is sent successfully.')
    return redirect('home_page')
  else:
    return redirect('home_page')

@login_required
def unfollow(request, profileID):
    from_profile = request.user.profile
    to_profile = Profile.objects.get(pk=profileID)
    from_profile.friends.remove(to_profile)
    to_profile.friends.remove(from_profile)
    return redirect('home_page')

@login_required
def accept_follow_request(request, follow_request_id):
  follow_request = ProfileFollowRequest.objects.get(id=follow_request_id)
  if follow_request.following_profile_id == request.user.profile:
    follow_request.profile_id.friends.add(follow_request.following_profile_id)
    follow_request.following_profile_id.friends.add(follow_request.profile_id)
    follow_request.delete()
    return redirect('home_page')
  else:
    return redirect('home_page')

@login_required
def decline_follow_request(request, follow_request_id):
  follow_request = ProfileFollowRequest.objects.get(id=follow_request_id)
  if follow_request.following_profile_id == request.user.profile:
    follow_request.delete()
    return redirect('home_page')
  else:
    return redirect('home_page')

@login_required
def cancel_follow_request(request, follow_request_id):
  follow_request = ProfileFollowRequest.objects.get(id=follow_request_id)
  if follow_request.profile_id == request.user.profile:
    follow_request.delete()
    return redirect('home_page')
  else:
    return redirect('home_page')

@login_required
def profile_friends_view(request, profileID, *args, **kwargs):
  # current_profile = request.user.profile
  obj = Profile.objects.get(pk=profileID)
  friend_list = obj.friends.all()
  content = {"object": obj, "object_list": friend_list}
  return render(request, "profiles/friends.html", content)

@login_required
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
      spend_participant_credit(from_profile.id, to_offer.id)
      messages.success(request, 'Your join request is sent successfully.')
      return redirect('home_page')
    else:
      messages.info(request, 'You cannot send a join request to this offer')
      return redirect('home_page')
  else:
    messages.info(request, 'You cannot send a join request to this offer')
    return redirect('home_page')

@login_required
def accept_join_request(request, join_request_id):
  join_request = ProfileJoinOfferRequest.objects.get(id=join_request_id)
  if join_request.offer.owner == request.user.profile:
    # add profile to offer's participants
    join_request.offer.participants.add(join_request.profile)
    # add offer to profile's accepted offers
    join_request.profile.accepted_offers.add(join_request.offer)

    # deduct credits from the participant
    # if join_request.profile.credit < join_request.offer.credit:
    #   Profile.objects.filter(pk=join_request.profile.id).update(credit=0.00)
    # else:
    #   remaining_credits = join_request.profile.credit - join_request.offer.credit
    #   Profile.objects.filter(pk=join_request.profile.id).update(credit=remaining_credits)

    # join_request.delete()
    join_request.is_accepted = True
    join_request.save()
    return redirect('home_page')
  else:
    return redirect('home_page')

@login_required
def decline_join_request(request, join_request_id):
  join_request = ProfileJoinOfferRequest.objects.get(id=join_request_id)
  if join_request.offer.owner == request.user.profile:
    retract_participant_credit(join_request.profile.id, join_request.offer.id)
    join_request.is_accepted = False
    # join_request.delete()
    return redirect('home_page')
  else:
    return redirect('home_page')

@login_required
def cancel_join_request(request, join_request_id):
  join_request = ProfileJoinOfferRequest.objects.get(id=join_request_id)
  if join_request.profile == request.user.profile:
    retract_participant_credit(join_request.profile.id, join_request.offer.id)
    join_request.delete()
  return redirect('home_page')

def unanswered_join_request(join_request_id):
  join_request = ProfileJoinOfferRequest.objects.get(id=join_request_id)
  utc = pytz.UTC
  now = datetime.datetime.now().replace(tzinfo=utc)
  if now > join_request.offer.app_deadline:
    retract_participant_credit(join_request.profile.id, join_request.offer.id)
    join_request.delete()

@login_required
def leave_offer(request, offerID):
  offer = Offer.objects.get(pk=offerID)
  if request.user.profile in offer.participants.all():
    utc = pytz.UTC
    now = datetime.datetime.now().replace(tzinfo=utc)
    # check if cancellation deadline has passed if we do not handle it anywhere else
    if now < offer.cancel_deadline:
      # give profile's credits back
      retract_participant_credit(request.user.profile.id, offer.id)
    # offer_creds = offer.credit
    # profile_creds = request.user.profile.credit
    # Profile.objects.filter(pk=request.user.profile.id).update(credit=offer_creds + profile_creds)


    # remove profile from offer participants
    offer.participants.remove(request.user.profile)
    # remove the offer from profile's accepted offers
    request.user.profile.accepted_offers.remove(offer)
    return redirect('home_page')

@login_required
def rate_finished_offer(request, offerID, *args, **kwargs):
  obj = request.user.profile
  o = Offer.objects.get(pk=offerID)

  if request.method == 'POST':
    form = ReviewForm(request.POST)
    if form.is_valid():
      review = form.save(commit=False)
      review.review_giver = request.user.profile
      review.offer = o
      rate = form.cleaned_data['rating']
      review.rating = rate
      form.save()
      return redirect('home_page')
  else:
    form = ReviewForm()

  return render(request, 'profiles/rate_offer_form.html', {'object': obj, 'offer': o, 'form': form})

@login_required
def approve_finished_offer(request, offerID, *args, **kwargs):
  offer = Offer.objects.get(pk=offerID)
  if request.method == 'POST':
    form = ApproveForm(request.POST)
    if form.is_valid():
      approval = form.cleaned_data['offer_done']
      if approval == 'Approve':
        Offer.objects.filter(pk=offerID, approval_status='Outstanding').update(approval_status='Approved')
        messages.info(request, 'You approved that you provided this offer.')
      else:
        Offer.objects.filter(pk=offerID, approval_status='Outstanding').update(approval_status='Declined')
        messages.info(request, 'You declined that you provided this offer.')
      return redirect('home_page')
  else:
    form = ApproveForm()
  return render(request, 'profiles/approve_offer.html', {'object': offer, 'form': form})

@login_required
def rate_participant(request, offerID, participantID, *args, **kwargs):
  o = Offer.objects.get(pk=offerID)
  p = o.participants.get(pk=participantID)
  if request.method == 'POST':
    form = OwnerToParticipantReviewForm(request.POST)
    rate = form.save(commit=False)
    rate.offer = o
    rate.participant = p
    r = form.cleaned_data['rating']
    rate.rating = r
    rate.save()
    return redirect('offer_look', pk=offerID)
  else:
    form = OwnerToParticipantReviewForm()
  return render(request, 'profiles/rate_participant_form.html', {'form': form, 'offer': o, 'participant': p})

def automatic_offer_review(profile, offerID, *args, **kwargs):
  offer = Offer.objects.get(pk=offerID)
  day_limit = 3
  # if day_limit days have passed since the end date of the offer and participant didn't review, review automatically
  utc = pytz.UTC
  now = datetime.datetime.now().replace(tzinfo=utc)
  if now - offer.end_date > datetime.timedelta(days=day_limit) and profile in offer.participants.all():
    review, created = ProfileReview.objects.get_or_create(review_giver=profile, offer=offer)
    if created:
      return True
  return False

def automatic_offer_approval(offerID):
  offer = Offer.objects.get(pk=offerID)
  day_limit = 3
  # if day_limit days have passed since the end date of the offer and owner didn't approve, decline automatically
  utc = pytz.UTC
  now = datetime.datetime.now().replace(tzinfo=utc)
  if now - offer.end_date > datetime.timedelta(days=day_limit):
    if offer.approval_status == 'Outstanding':
      Offer.objects.filter(pk=offerID, approval_status='Outstanding').update(approval_status='Declined')
      return True
  return False

def spend_participant_credit(profileID, offerID):
  offer = Offer.objects.get(pk=offerID)
  profile = Profile.objects.get(pk=profileID)
  current_cred = profile.credit
  Profile.objects.filter(pk=profileID).update(credit=current_cred - offer.credit)

def retract_participant_credit(profileID, offerID):
  offer = Offer.objects.get(pk=offerID)
  profile = Profile.objects.get(pk=profileID)
  current_cred = profile.credit
  Profile.objects.filter(pk=profileID).update(credit=current_cred + offer.credit)

def handle_credit_after_offer(offerID):
  offer = Offer.objects.get(pk=offerID)
  participants = offer.participants.all()
  # if offer is finished and it is a service and owner approved it
  if offer.offer_type == 'Service' and offer.offer_status == 'Passive' and offer.approval_status == 'Approved':
  # check for each participant if he/she approved the offer as well
    for p in participants:
      review = ProfileReview.objects.get(review_giver=p, offer=offer)
      # if there is a mutual handshake, transfer the credits from participant to owner
      if review.done:
        # add credits to offer owner
        current_offer_owner_credits = offer.owner.credit
        Profile.objects.filter(pk=offer.owner.id).update(credit=current_offer_owner_credits + offer.credit)
      # if participant did not approve it, give credits back
      else:
        retract_participant_credit(p.id, offer.id)

def waste_credit():
  pass