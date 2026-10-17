from django.urls import path

from . import views

app_name = 'skills'

urlpatterns = [
    path('explore/', views.ExploreView.as_view(), name='explore'),
    path('popular/', views.PopularView.as_view(), name='popular'),
    path('categories/', views.CategoryListView.as_view(), name='categories'),
    path('categories/<slug:slug>/', views.CategoryDetailView.as_view(), name='category_detail'),
    path('offers/new/', views.OfferCreateView.as_view(), name='offer_create'),
    path('offers/<int:pk>/', views.OfferDetailView.as_view(), name='offer_detail'),
    path('offers/<int:pk>/edit/', views.OfferUpdateView.as_view(), name='offer_edit'),
    path('offers/<int:pk>/delete/', views.OfferDeleteView.as_view(), name='offer_delete'),
    path('offers/<int:pk>/submit/', views.OfferSubmitView.as_view(), name='offer_submit'),
    path('offers/<int:pk>/revise/', views.OfferReviseView.as_view(), name='offer_revise'),
    path('offers/<int:pk>/revise/discard/', views.OfferRevisionDiscardView.as_view(), name='revision_discard'),
    path('my-offers/', views.MyOffersView.as_view(), name='my_offers'),
    path('offers/<int:pk>/favorite/', views.FavoriteToggleView.as_view(), name='favorite_toggle'),
    path('favorites/', views.FavoritesView.as_view(), name='favorites'),
]

