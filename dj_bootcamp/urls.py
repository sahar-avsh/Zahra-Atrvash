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
    profile_notifications_view,
    profile_friends_view,
    profile_edit_view,
    profile_activity_background_view,
    send_join_request,
    accept_join_request,
    decline_join_request,
    cancel_join_request,
    leave_offer,
    send_follow_request,
    accept_follow_request,
    decline_follow_request,
    unfollow,
    cancel_follow_request
)

from offers.views import (
    offer_create_view,
    offer_outlook_view,
    cancel_offer_view
)

urlpatterns = [
    path('timeline/', home_view, name='home_page'),
    path('send_follow_request/<str:profileID>/', send_follow_request, name='send_follow_request'),
    path('accept_follow_request/<int:follow_request_id>/', accept_follow_request, name='accept_follow_request'),
    path('decline_follow_request/<int:follow_request_id>/', decline_follow_request, name='decline_follow_request'),
    path('unfollow/<str:profileID>/', unfollow, name='unfollow'),
    path('cancel_friend_request/<str:follow_request_id>', cancel_follow_request, name='cancel_follow_request'),
    path('notifications/', profile_notifications_view, name='notifications'),
    path('friends/<str:profileID>/', profile_friends_view, name='friends'),
    path('activity-background/<str:profileID>/', profile_activity_background_view, name='activity_background'),
    path('profiles/<str:pk>/look/', profile_outlook_view, name='profile_look'),
    path('profiles/edit/', profile_edit_view, name='edit_view'),
    # path('api/profiles/<str:pk>/', profile_api_detail_view),
    path('admin/', admin.site.urls),
    path('offers/<str:pk>/look/', offer_outlook_view, name='offer_look'),
    path('offers/create/', offer_create_view, name='offer_create'),
    path('send_join_request/<str:offerID>/', send_join_request, name='send_join_request'),
    path('accept_join_request/<int:join_request_id>/', accept_join_request, name='accept_join_request'),
    path('decline_join_request/<int:join_request_id>/', decline_join_request, name='decline_join_request'),
    path('cancel_join_request/<int:join_request_id>/', cancel_join_request, name='cancel_join_request'),
    path('cancel_offer/<str:offerID>/', cancel_offer_view, name='cancel_offer'),
    path('leave_offer/<str:offerID>/', leave_offer, name='leave_offer'),
    #path('accounts/logout/', LogoutView.as_view(), name='logout'),
    #path('accounts/login/', LoginView.as_view(), name='login'),
    #path('accounts/signup/', SignupView.as_view(), name='signup')
    re_path(r'^accounts/', include('allauth.urls'))
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
