from django.urls import path

from . import views

app_name = 'moderation'

urlpatterns = [
    path('', views.ModerationQueueView.as_view(), name='queue'),
    path('offers/<int:pk>/', views.OfferModerateView.as_view(), name='offer'),
    path('revisions/<int:pk>/', views.RevisionModerateView.as_view(), name='revision'),
    path('users/', views.UserListView.as_view(), name='users'),
    path(
        'users/<int:pk>/<str:action>/',
        views.UserActionView.as_view(),
        name='user_action',
    ),
]

