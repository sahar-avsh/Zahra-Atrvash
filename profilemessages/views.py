from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q

from profilemessages.forms import MessageSearchForm, ProfileMessageForm

from profilemessages.models import ProfileMessage

from profiles.models import Profile

# Create your views here.
@login_required
def send_message_view(request, profileID, *args, **kwargs):
  to = Profile.objects.get(pk=profileID)
  if request.method == 'POST':
    form = ProfileMessageForm(request.POST)
    message = form.save(commit=False)
    message.message_to = to
    message.message_from = request.user.profile
    message.save()
    messages.success(request, 'Message sent successfully.')
    return redirect('home_page')
  else:
    form = ProfileMessageForm()
  return render(request, 'messages/send_message.html', {'form': form, 'to': to})

@login_required
def inbox_view(request, *args, **kwargs):
  if request.method == 'POST':
    form = MessageSearchForm(request.POST)
    if form.is_valid():
      search_flag = True
      arg = form.cleaned_data['text']
      if arg:
        qs = ProfileMessage.objects.filter(Q(message_from__f_name__icontains=arg) | Q(message_from__l_name__icontains=arg) | Q(title__icontains=arg) | Q(body__icontains=arg)).exclude(message_from=request.user.profile)
      else:
        qs = ProfileMessage.objects.filter(message_to=request.user.profile)
  else:
    form = MessageSearchForm()
    qs = ProfileMessage.objects.filter(message_to=request.user.profile)
    search_flag = False

  content = {
    'object_list': qs,
    'form': form,
    'flag': search_flag
  }
  return render(request, 'messages/inbox_view.html', content)

@login_required
def sent_messages_view(request, *args, **kwargs):
  if request.method == 'POST':
    form = MessageSearchForm(request.POST)
    if form.is_valid():
      search_flag = True
      arg = form.cleaned_data['text']
      if arg:
        qs = ProfileMessage.objects.filter(Q(message_to__f_name__icontains=arg) | Q(message_to__l_name__icontains=arg) | Q(title__icontains=arg) | Q(body__icontains=arg)).exclude(message_to=request.user.profile)
      else:
        qs = ProfileMessage.objects.filter(message_from=request.user.profile)
  else:
    form = MessageSearchForm()
    qs = ProfileMessage.objects.filter(message_from=request.user.profile)
    search_flag = False

  content = {
    'object_list': qs,
    'form': form,
    'flag': search_flag
  }
  return render(request, 'messages/sent_messages_view.html', content)