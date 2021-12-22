from django.core.exceptions import ValidationError
from django.http.response import HttpResponse, JsonResponse, Http404, HttpResponseRedirect
from django.shortcuts import render, redirect

from .forms import ProfileModelForm
from .models import Profile

# Create your views here.
def home_view(request, *args, **kwargs):
  # return HttpResponse("<h1>Hello World!<h1>")
  context = {"name": "Sahari Curly Atrvash"}
  return render(request, "home.html", context)

""" def profile_create_view(request, *args, **kwargs):
  if request.method == 'POST':
    post_data = request.POST or None
    if post_data != None:
      my_form = ProfileForm(request.POST)
      if my_form.is_valid():
        print(my_form.cleaned_data.get('name'))
        name_input = my_form.cleaned_data.get('name')
        # Profile.objects.create(name=name_input)
        # print('post_data', post_data)
  return render(request, 'forms.html', {}) """

def profile_edit_view(request, *args, **kwargs):
  
  form = ProfileModelForm(request.POST or None)
  if form.is_valid():
    # obj = form.save(commit=False)
    # obj.save()
    data = form.cleaned_data
    # Profile.objects.create(**data)
    form = ProfileModelForm()
    # return HttpResponseRedirect("/success") --> To let user know profile is successfully created
    # return redirect("/success") 
  return render(request, "forms.html", {'form': form})


""" def profile_detail_view(request, pk, *args, **kwargs):
  try:
      obj = Profile.objects.get(pk=pk)
  except (Profile.DoesNotExist, ValidationError):
      raise Http404  # render html page with HTTP status code of 404
  # text = f"Hello, It's {obj.f_name} {obj.l_name}. I am living at {obj.loc_ltd}, {obj.loc_long} and working as a {obj.occupation} with a {obj.education}"
  # return HttpResponse(text)
  return render(request, "profiles/detail.html", {"object": obj}) """


""" def profile_outlook_view(request, pk, *args, **kwargs):
  skill_list = Skill.objects.filter(user=pk)
  interest_list = Interest.objects.filter(user=pk)
  try:
    obj = Profile.objects.get(pk=pk)
  except (Profile.DoesNotExist, ValidationError):
    raise Http404
  return render(request, "profiles/outlook.html", {"object": obj,
   "skill_list": skill_list, "interest_list": interest_list}) """


def profile_list_view(request, *args, **kwargs):
  qs = Profile.objects.all()
  context = {"object_list": qs}
  return render(request, "profiles/list.html", context)


""" def profile_api_detail_view(request, pk, *args, **kwargs):
  try:
      obj = Profile.objects.get(pk=pk)
  except (Profile.DoesNotExist, ValidationError):
      return JsonResponse(
          {"Message": "Not found!"}, status=404
      )  # render JSON with HTTP status code of 404
  return JsonResponse({"First name": obj.f_name}) """
