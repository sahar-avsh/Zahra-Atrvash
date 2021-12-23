"""dj_bootcamp URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, re_path, include

from django.conf.urls.static import static
from django.conf import settings
from offers.models import Offer

from allauth.account.views import LoginView, SignupView, LogoutView

from profiles.views import (
    home_view,
    # profile_outlook_view,
    profile_outlook_view,
    profile_list_view,
)

from offers.views import (
    offer_create_view,
    offer_outlook_view,
)

urlpatterns = [
    path('timeline/', home_view, name='home_page'),
    # path('profiles/', profile_list_view),
    path('profiles/<str:pk>/look/', profile_outlook_view, name='profile_look'),
    # path('profiles/600cf81f-bf63-404a-9231-618e4f7d952f/', views.profile_detail_view),
    # path('profiles/<str:pk>/', profile_detail_view),
    # path('profiles/<str:pk>/look/', profile_outlook_view),
    # path('api/profiles/<str:pk>/', profile_api_detail_view),
    path('admin/', admin.site.urls),
    path('offers/<str:pk>/look/', offer_outlook_view, name='offer_look'),
    path('offers/create/', offer_create_view, name='offer_create'),
    #path('accounts/logout/', LogoutView.as_view(), name='logout'),
    #path('accounts/login/', LoginView.as_view(), name='login'),
    #path('accounts/signup/', SignupView.as_view(), name='signup')
    re_path(r'^accounts/', include('allauth.urls'))
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
