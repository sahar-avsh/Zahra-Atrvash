from django.core.exceptions import ValidationError
from django.forms.fields import NullBooleanField
from django.http.response import HttpResponse, JsonResponse, Http404, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.contrib import messages
from django.db.models.signals import post_save

from allauth.account.signals import user_signed_up, user_logged_in
from django.dispatch import receiver

from categorytags.forms import InterestForm, SkillForm
from offers.forms import ApproveForm

from .forms import OwnerToParticipantReviewForm, ProfileModelForm, ProfileSearchForm, ReviewForm
from .models import Profile, ProfileFollowRequest, ProfileJoinOfferRequest, ProfileReview, OwnerToParticipantReview
from offers.models import Offer
from categorytags.models import Skill, Interest

from django.db.models import Q
import pytz
import datetime
from geopy.distance import great_circle
from itertools import chain

# Create your views here.


#****************************** Sign-up functionality **************************************************
@receiver(user_signed_up)
def after_user_signed_up(user, **kwargs):
  profile = Profile.objects.create(user=user, f_name=user.first_name, l_name=user.last_name)





@receiver(user_logged_in)
def after_user_signed_in(user, **kwargs):
  qs_offers = Offer.objects.all()
  for i in qs_offers:
    r1 = automatic_offer_approval(i.id)
    r2 = automatic_offer_review(user.profile, i.id)

  qs_join_requests = ProfileJoinOfferRequest.objects.filter(profile=user.profile)
  for r in qs_join_requests:
    unanswered_join_request(r.id)





# method for updating credit
@receiver(post_save, sender=ProfileReview)
@receiver(post_save, sender=Offer)
#@receiver(post_save)
def update_credit(sender, instance=None, created=False, **kwargs):
  if sender.__name__ == 'ProfileReview':
    # if profile review is saved, check if that offer was approved

    # provider approved, participant accepted --> provider gets credit
    if instance.done == True and instance.offer.approval_status == 'Approved':
      current_provider_creds = instance.offer.owner.credit
      Profile.objects.filter(pk=instance.offer.owner.id).update(credit=current_provider_creds + instance.offer.credit)
    # provider declined, participant accepted --> waste of credit

    # no matter what provider says, if participant declines, gets credit back
    # provider declined, participant declined --> participant gets credit back
    # provider approved, participant declined --> participant gets credit back
    elif not instance.done == True:
      retract_participant_credit(instance.review_giver.id, instance.offer.id)

  else:
    # if offer is saved, check if provider approved the offer
    approval = instance.approval_status
    # provider approved
    if approval == 'Approved':
      for i in instance.participants:
        try:
          review = ProfileReview.objects.get(review_giver=i, offer=instance)
          # participant approved --> provider gets credit
          if review.done:
            current_provider_creds = instance.owner.credit
            Profile.objects.filter(pk=instance.owner.id).update(credit=current_provider_creds + instance.credit)
          # participant declined --> gets credit back
          else:
            retract_participant_credit(i.id, instance.id)
        except ProfileReview.DoesNotExist:
          pass
    # provider declined
    elif approval == 'Declined':
      for j in instance.participants.all():
        try:
          review = ProfileReview.objects.get(review_giver=j, offer=instance)
          # participant accepted --> waste
          # participant declined --> gets credit back
          if not review.done:
            retract_participant_credit(j.id, instance.id)
        except ProfileReview.DoesNotExist:
          pass





#****************************** Rules & Navigation page functionality **************************************************
@login_required
def home_view(request, *args, **kwargs):
  return render(request, 'home.html')







#  ****************************** Rate & Review page functionality ****************************************************
@login_required
def profile_rate_reviews_view(request, profileID, *args, **kwargs):
  tz = pytz.timezone('Europe/Istanbul')
  now = datetime.datetime.now().replace(tzinfo=tz)

  obj = Profile.objects.get(pk=profileID)
  passive_offers = Offer.objects.filter(owner=obj, is_cancelled=False, end_date__lt=now)
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
    avg_rating = round(total / total_number_reviews, 1)
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





#****************************** Profile creation and edition page functionality *****************************************
@login_required
def profile_edit_view(request, *args, **kwargs):
  profile = request.user.profile
  qs_skills = profile.skills.all()
  qs_interests = profile.interests.all()

  if request.method == 'POST':
    form = ProfileModelForm(request.POST, request.FILES, instance=profile)
    form_skill = SkillForm(request.POST)
    form_interest = InterestForm(request.POST)

    if form.is_valid():
      profile = form.save(commit=False)
      if form.cleaned_data['location']:
        loc = form.cleaned_data['location']
        # loc_elements = loc.split(',')
        # profile.loc_long = loc_elements[0]
        # profile.loc_ltd = loc_elements[1]
        profile.loc_ltd = loc[1]
        profile.loc_long = loc[0]
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




#****************************** Profile outlook page functionality *****************************************
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
  except ProfileFollowRequest.DoesNotExist:
    current_profile_friend_request = None

  try:
    reverse_friend_request = ProfileFollowRequest.objects.get(profile_id=obj, following_profile_id=current_profile)
  except ProfileFollowRequest.DoesNotExist:
    reverse_friend_request = None

  return render(request, "profiles/outlook.html", {"object": obj, "user": current_profile,
   "skill_list": skill_list, "interest_list": interest_list, 'friend_list': friend_list, 
   'user_friend_list': current_profile_friend_list, 'user_friend_request': current_profile_friend_request,
  'address_flag': address_flag, 'address': address, 'reverse_friend_request': reverse_friend_request})




#****************************** Getting address from the map functionality *********************************
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





#****************************** Notification page functionality *********************************
@login_required
def profile_notifications_view(request, *args, **kwargs):
  tz = pytz.timezone('Europe/Istanbul')
  now = datetime.datetime.now().replace(tzinfo=tz)
  current_profile = request.user.profile
  active_offers_of_current_profile = Offer.objects.filter(owner=current_profile, is_cancelled=False, app_deadline__gt=now)

  # friend requests
  friend_requests = ProfileFollowRequest.objects.filter(following_profile_id=current_profile).order_by('-created_at')
  # join requests to your offers
  join_requests_to_profile = ProfileJoinOfferRequest.objects.filter(offer__in=active_offers_of_current_profile, is_accepted=None).order_by('offer__app_deadline', '-created_at')
  # outstanding approvals for offers finished as an offer provider
  outstanding_approvals = Offer.objects.filter(owner=current_profile, end_date__lt=now, approval_status='Outstanding', is_cancelled=False).order_by('end_date')
  # outstanding reviews for offers finished as a participant
  reviews_done = ProfileReview.objects.filter(review_giver=current_profile).values_list('offer', flat=True)
  outstanding_reviews = current_profile.accepted_offers.filter(end_date__lt=now).exclude(pk__in=[o for o in reviews_done]).order_by('end_date')
  # join requests that current profile has sent and that got accepted
  join_requests_accepted = ProfileJoinOfferRequest.objects.filter(profile=current_profile, is_accepted=True, offer__start_date__gt=now).order_by('offer__start_date')
  # join requests that current profile has sent and that got declined
  join_requests_declined = ProfileJoinOfferRequest.objects.filter(profile=current_profile, is_accepted=False, offer__start_date__gt=now).order_by('offer__start_date')
  # joined or requested offers that got cancelled
  join_requests_offer_cancelled = ProfileJoinOfferRequest.objects.filter(profile=current_profile, is_accepted=None, offer__is_cancelled=True, offer__start_date__gt=now)
  joined_offers_cancelled = current_profile.accepted_offers.filter(is_cancelled=True, start_date__gt=now)

  content = {"friend_requests": friend_requests, 'join_requests_to_profile': join_requests_to_profile,
  'outstanding_approvals': outstanding_approvals,
  'outstanding_reviews': outstanding_reviews, 'join_requests_accepted': join_requests_accepted,
  'join_requests_declined': join_requests_declined, 'join_requests_offer_cancelled': join_requests_offer_cancelled,
  'joined_offers_cancelled': joined_offers_cancelled}
  return render(request, "profiles/notifications.html", content)





#************************** Activity background page functionality *******************************
@login_required
def profile_activity_background_view(request, profileID, *args, **kwargs):
  tz = pytz.timezone('Europe/Istanbul')
  now = datetime.datetime.now().replace(tzinfo=tz)

  obj = Profile.objects.get(pk=profileID)
  created_active_offers = Offer.objects.filter(owner=obj, start_date__gt=now, is_cancelled=False).order_by('start_date')
  cancelled_or_passive_offers = Offer.objects.filter(Q(owner=obj) & (Q(end_date__lt=now) | Q(is_cancelled=True))).order_by('start_date')
  joined_offers = obj.accepted_offers.all().order_by('-start_date')

  outstanding_offer_requests = ProfileJoinOfferRequest.objects.filter(profile=obj, is_accepted=None, offer__app_deadline__gt=now).order_by('offer__start_date')

  content = {'created_active_offers': created_active_offers,
  'cancelled_passive_offers': cancelled_or_passive_offers,
  'joined_offers': joined_offers,
  'outstanding_offers': outstanding_offer_requests, 'obj': obj}
  return render(request, "profiles/activity_background.html", content)




#**************************** Follow request functionality ******************************
@login_required
def send_follow_request(request, profileID):
  from_profile = request.user.profile
  to_profile = Profile.objects.get(pk=profileID)
  follow_request, created = ProfileFollowRequest.objects.get_or_create(
    profile_id=from_profile, following_profile_id=to_profile
  )
  if created:
    messages.success(request, 'Your follow request is sent successfully.')
  else:
    messages.info(request, 'There is a pending follow request.')
  return redirect('profile_look', pk=to_profile.id)


  
#****************************** Unfriend functionality *********************************
@login_required
def unfollow(request, profileID):
    from_profile = request.user.profile
    to_profile = Profile.objects.get(pk=profileID)
    from_profile.friends.remove(to_profile)
    to_profile.friends.remove(from_profile)
    messages.success(request, f'You have unfollowed {to_profile.f_name}.')
    return redirect('friends', profileID=request.user.profile.id)


#*********************** Accepting follow request functionality ************************
@login_required
def accept_follow_request(request, follow_request_id):
  follow_request = ProfileFollowRequest.objects.get(id=follow_request_id)
  if follow_request.following_profile_id == request.user.profile:
    follow_request.profile_id.friends.add(follow_request.following_profile_id)
    follow_request.following_profile_id.friends.add(follow_request.profile_id)
    follow_request.delete()
    messages.success(request, f'You have accepted this follow request. You are friends with {follow_request.profile_id.f_name}')
  return redirect('profile_look', pk=follow_request.profile_id.id)


#*********************** Declining follow request functionality ************************
@login_required
def decline_follow_request(request, follow_request_id):
  follow_request = ProfileFollowRequest.objects.get(id=follow_request_id)
  if follow_request.following_profile_id == request.user.profile:
    follow_request.delete()
    messages.success(request, 'You have declined this follow request.')
  return redirect('profile_look', pk=follow_request.profile_id.id)


#******************** Canceling the sent follow request functionality ********************
@login_required
def cancel_follow_request(request, follow_request_id):
  follow_request = ProfileFollowRequest.objects.get(id=follow_request_id)
  if follow_request.profile_id == request.user.profile:
    follow_request.delete()
    messages.success(request, 'You have cancelled your follow request.')
  return redirect('profile_look', pk=follow_request.following_profile_id.id)



#******** Profile view of other user rather than the active one functionality *************
@login_required
def profile_friends_view(request, profileID, *args, **kwargs):
  obj = Profile.objects.get(pk=profileID)
  friend_list = obj.friends.all()
  if request.method == 'POST':
    form = ProfileSearchForm(request.POST)
    if form.is_valid():
      search_flag = True
      keywords = [word.strip() for word in form.cleaned_data['name'].split() if word.strip() != '']
      all_hits = Profile.objects.none()
      if len(keywords) > 0:
        for arg in keywords:
          if obj.id == request.user.profile.id:
            all_hits = all_hits | Profile.objects.filter(Q(f_name__icontains=arg) | Q(l_name__icontains=arg)).exclude(pk=profileID)
          else:
            all_hits = all_hits | friend_list.filter(Q(f_name__icontains=arg) | Q(l_name__icontains=arg))
        all_hits = all_hits.distinct()
  else:
    form = ProfileSearchForm()
    all_hits = Profile.objects.none()
    search_flag = False

  existing_follow_requests_profile = ProfileFollowRequest.objects.filter(profile_id=request.user.profile).values_list('following_profile_id', flat=True)
  existing_follow_requests_to_profile = ProfileFollowRequest.objects.filter(following_profile_id=request.user.profile).values_list('profile_id', flat=True)

  existing_follow_requests_a = ProfileFollowRequest.objects.filter(profile_id=request.user.profile)
  existing_follow_requests_dict = {}
  for i in existing_follow_requests_a:
    existing_follow_requests_dict[i.following_profile_id] = i.id

  existing_follow_requests_b = ProfileFollowRequest.objects.filter(following_profile_id=request.user.profile)
  existing_follow_requests_to_profile_dict = {}
  for j in existing_follow_requests_b:
    existing_follow_requests_to_profile_dict[j.profile_id] = j.id

  content = {
    'object': obj,
    'object_list': all_hits,
    'friend_list': friend_list,
    'form': form,
    'flag': search_flag,
    'existing_follow_requests': existing_follow_requests_profile,
    'follow_requests_dict': existing_follow_requests_dict,
    'existing_follow_requests_to_profile': existing_follow_requests_to_profile,
    'follow_requests_to_profile_dict': existing_follow_requests_to_profile_dict,
  }
  return render(request, "profiles/friends.html", content)


#******************** Applying for an offer functionality ********************
@login_required
def send_join_request(request, offerID, *args, **kwargs):
  from_profile = request.user.profile
  to_offer = Offer.objects.get(pk=offerID)

  # check if profile has enough credits to join this offer
  available_credits = from_profile.credit
  required_credits = to_offer.credit
  # also check if offer has enough capacity
  num_of_participants = to_offer.participants.count()

  if to_offer.offer_type == 'Service':
    if available_credits >= required_credits and num_of_participants < to_offer.capacity and to_offer.can_apply:
      join_request, created = ProfileJoinOfferRequest.objects.get_or_create(
      profile=from_profile, offer=to_offer, is_accepted=None
    )
      if created:
        spend_participant_credit(from_profile.id, to_offer.id)
        messages.success(request, 'Your join request is sent successfully.')
        return redirect('timeline')
      else:
        messages.info(request, 'You cannot send a join request to this offer')
        return redirect('timeline')
    else:
      messages.info(request, 'You cannot send a join request to this offer')
      return redirect('timeline')
  else:
    if num_of_participants < to_offer.capacity and to_offer.can_apply:
      to_offer.participants.add(from_profile)
      from_profile.accepted_offers.add(to_offer)
    else:
      messages.error(request, 'You cannot join this event.')
    return redirect('timeline')


#******************** Accepting join requests for an offer functionality ********************
@login_required
def accept_join_request(request, join_request_id):
  join_request = ProfileJoinOfferRequest.objects.get(id=join_request_id)
  if join_request.offer.owner == request.user.profile and join_request.offer.can_apply:
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
  return redirect('profile_look', pk=join_request.profile.id)



#******************** Declining join requests for an offer  ********************
@login_required
def decline_join_request(request, join_request_id):
  join_request = ProfileJoinOfferRequest.objects.get(id=join_request_id)
  if join_request.offer.owner == request.user.profile:
    retract_participant_credit(join_request.profile.id, join_request.offer.id)
    join_request.is_accepted = False
    join_request.save()
    # join_request.delete()
  return redirect('profile_look', pk=join_request.profile.id)



#******************** Canceling a sent request for an offer  ********************
@login_required
def cancel_join_request(request, join_request_id):
  join_request = ProfileJoinOfferRequest.objects.get(id=join_request_id)
  if join_request.profile == request.user.profile and join_request.offer.can_cancel:
    retract_participant_credit(join_request.profile.id, join_request.offer.id)
    join_request.delete()
  return redirect('timeline')

#******************** Handling unanswered requests for an offer  ********************
def unanswered_join_request(join_request_id):
  join_request = ProfileJoinOfferRequest.objects.get(id=join_request_id)
  tz = pytz.timezone('Europe/Istanbul')
  now = datetime.datetime.now().replace(tzinfo=tz)
  if now > join_request.offer.app_deadline:
    retract_participant_credit(join_request.profile.id, join_request.offer.id)
    join_request.delete()


#******************** Leaving an offer that I had been accepted to  ********************
@login_required
def leave_offer(request, offerID):
  offer = Offer.objects.get(pk=offerID)
  if request.user.profile in offer.participants.all():
    # check if cancellation deadline has passed if we do not handle it anywhere else
    if offer.can_cancel:
      # give profile's credits back
      retract_participant_credit(request.user.profile.id, offer.id)
    else:
      pass # implement waste credit
    
    # remove profile from offer participants
    offer.participants.remove(request.user.profile)
    # remove the offer from profile's accepted offers
    request.user.profile.accepted_offers.remove(offer)
  return redirect('timeline')


#******************** Rating a finished offer functionality ********************
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
      done = form.cleaned_data['done']
      review.done = done
      rate = form.cleaned_data['rating']
      review.rating = rate
      review.save()
      return redirect('home_page')
  else:
    form = ReviewForm()

  return render(request, 'profiles/rate_offer_form.html', {'object': obj, 'offer': o, 'form': form})


#******************** Shaking hands from both parties for a finished offer  ********************
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


#******************** Rating participants by the offer provider  ********************
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
  tz = pytz.timezone('Europe/Istanbul')
  now = datetime.datetime.now().replace(tzinfo=tz)
  if now - offer.end_date > datetime.timedelta(days=day_limit) and profile in offer.participants.all():
    review, created = ProfileReview.objects.get_or_create(review_giver=profile, offer=offer)
    if created:
      review.done = False
      return True
  return False


#******************** Automatic offer approval for the taken offer if participant does not approve after 3 days  ********************
def automatic_offer_approval(offerID):
  offer = Offer.objects.get(pk=offerID)
  day_limit = 3
  # if day_limit days have passed since the end date of the offer and owner didn't approve, decline automatically
  tz = pytz.timezone('Europe/Istanbul')
  now = datetime.datetime.now().replace(tzinfo=tz)
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


#******************** credit transmition functionality ********************
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