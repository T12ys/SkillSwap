from django.urls import path

from . import views

app_name = 'reviews'

urlpatterns = [
    path('requests/<int:pk>/review/', views.ReviewCreateView.as_view(), name='create'),
    path('reviews/<int:pk>/edit/', views.ReviewUpdateView.as_view(), name='edit'),
    path('reviews/<int:pk>/delete/', views.ReviewDeleteView.as_view(), name='delete'),
]

