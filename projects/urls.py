from django.urls import path

from . import views

app_name = 'projects'

urlpatterns = [
#    path('', views.IndexView.as_view(), name='index'),
    path('create/<str:type>', views.ProjectCreate.as_view(), name='create'),
    path('<int:pk>/update', views.ProjectUpdate.as_view(), name='update'),
    path('<int:pk>/delete', views.ProjectDelete.as_view(), name='delete'),
    path('<int:pk>/', views.ProjectDetails.as_view(), name='details'),
    path('community/create/', views.CommunityCreate.as_view(), name='community_create'),
    path('community/<int:pk>', views.CommunityDetails.as_view(), name='community_details'),
    path('community/<int:pk>/update', views.CommunityUpdate.as_view(), name='community_update'),
    path('community/<int:pk>/delete', views.CommunityDelete.as_view(), name='community_delete'),
    path('community/', views.CommunityList.as_view(), name='community_list'),
    path('community/<int:community_id>/members/add/', views.community_member_add, name='community_member_add'),
    path('community/<int:community_id>/members/remove/<int:user_id>', views.community_member_remove, name='community_member_remove'),
    path('community/<int:pk>/members', views.CommunityMemberList.as_view(), name='community_member_list'),
    path('<int:project>/report/create/', views.ReportCreate.as_view(), name='report_create'),
    path('report/<int:pk>', views.ReportDetails.as_view(), name='report_details'),
    path('report/<int:pk>/update', views.ReportUpdate.as_view(), name='report_update'),
    path('report/<int:pk>/delete', views.ReportDelete.as_view(), name='report_delete'),
    path('<int:project>/report/list', views.ReportList.as_view(), name='report_list'),
    path('report/<int:pk>/vote-up', views.report_vote_up, name='report_vote_up'),
    path('report/<int:pk>/vote-down', views.report_vote_down, name='report_vote_down'),
    path('<int:project>/moneysupport/create', views.MoneySupportCreate.as_view(), name='money_support_create'),
    path('moneysupport/<int:pk>', views.MoneySupportDetails.as_view(), name='money_support_details'),
    path('moneysupport/<int:pk>/update', views.MoneySupportUpdate.as_view(), name='money_support_update'),
    path('<int:project_id>/timesupport/create', views.time_support_create, name='time_support_create'),
    path('timesupport/<int:pk>', views.TimeSupportDetails.as_view(), name='time_support_details'),
    path('timesupport/<int:pk>/update', views.TimeSupportUpdate.as_view(), name='time_support_update'),

    path('moneysupport/<int:pk>/delete', views.MoneySupportDelete.as_view(), name='moneysupport_delete'),
    path('timesupport/<int:pk>/delete', views.TimeSupportDelete.as_view(), name='timesupport_delete'),
    path('support/<int:pk>/<str:type>/accept', views.support_accept, name='support_accept'),
    path('support/<int:pk>/<str:type>/decline', views.support_decline, name='support_decline'),
    path('support/<int:pk>/<str:type>/delivered', views.support_delivered, name='support_delivered'),
    path('accounts/<int:user_id>/support/<str:type>/list', views.user_support_list, name='user_support_list'),

    path('accounts/<int:user_id>/photo/update', views.user_photo_update, name='user_photo_update'),
    path('accounts/<int:user_id>/vote/list', views.user_vote_list, name='user_vote_list'),
    path('user-autocomplete/', views.UserAutocomplete.as_view(), name='user_autocomplete'),
    path('<int:pk>/follow', views.follow_project, name='follow_project'),
    path('<int:project>/announcement/create/', views.AnnouncementCreate.as_view(), name='announcement_create'),
    path('announcement/<int:pk>', views.AnnouncementDetails.as_view(), name='announcement_details'),
    path('announcement_update/<int:pk>/update', views.AnnouncementUpdate.as_view(), name='announcement_update'),
    path('announcement/<int:pk>/delete', views.AnnouncementDelete.as_view(), name='announcement_delete'),
    path('<int:project_id>/necessity/time/update', views.time_necessity_update, name='time_necessity_update'),
    path('<int:project_id>/necessity/thing/update', views.thing_necessity_update, name='thing_necessity_update'),
    path('<int:project_id>/necessity/time', views.TimeNecessityList.as_view(), name='time_necessity_list'),
    path('necessity/time/<int:pk>', views.TimeNecessityDetails.as_view(), name='time_necessity_details'),
    path('necessity/thing/<int:pk>', views.ThingNecessityDetails.as_view(), name='thing_necessity_details'),
    path('<int:project_id>/necessity/thing', views.ThingNecessityList.as_view(), name='thing_necessity_list'),
    path('<int:project_id>/gallery/add', views.gallery_add, name='gallery_add'),
    path('<int:project_id>/gallery/update', views.gallery_update, name='gallery_update'),

]
