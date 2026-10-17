from django.urls import path, re_path

from . import views

app_name = 'bookings'

urlpatterns = [
    path('offers/<int:pk>/request/', views.RequestCreateView.as_view(), name='request_create'),
    path('requests/', views.MyRequestsView.as_view(), name='my_requests'),
    # only known actions
    re_path(
        r'^requests/(?P<pk>\d+)/(?P<action>accept|reject|complete|cancel)/$',
        views.RequestActionView.as_view(),
        name='request_action',
    ),
]

