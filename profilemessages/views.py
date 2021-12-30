from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required

from profilemessages.forms import ProfileMessageForm

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
  qs_received_messages = ProfileMessage.objects.filter(message_to=request.user.profile)
  return render(request, 'messages/inbox_view.html', {'object_list': qs_received_messages})

@login_required
def sent_messages_view(request, *args, **kwargs):
  qs_sent_messages = ProfileMessage.objects.filter(message_from=request.user.profile)
  return render(request, 'messages/sent_messages_view.html', {'object_list': qs_sent_messages})