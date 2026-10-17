import django_filters
from django import forms
from django.db.models import F
from django.db.models.functions import Lower

from .models import Category, SkillOffer

RATING_CHOICES = [
    (4, '4+ stars'),
    (3, '3+ stars'),
    (2, '2+ stars'),
]

SORT_CHOICES = [
    ('newest', 'Newest'),
    ('rating', 'Top rated'),
    ('reviews', 'Most reviewed'),
]


class OfferFilter(django_filters.FilterSet):
    q = django_filters.CharFilter(
        method='search',
        label='Search',
        widget=forms.TextInput(attrs={'type': 'search', 'placeholder': 'Search by title...'}),
    )
    category = django_filters.ModelChoiceFilter(
        queryset=Category.objects.all(),
        to_field_name='slug',
        empty_label='All categories',
    )
    level = django_filters.ChoiceFilter(
        choices=SkillOffer.Level.choices,
        empty_label='Any level',
    )
    format = django_filters.ChoiceFilter(
        choices=SkillOffer.Format.choices,
        empty_label='Online & offline',
    )
    min_rating = django_filters.ChoiceFilter(
        choices=RATING_CHOICES,
        method='filter_min_rating',
        empty_label='Any rating',
        label='Rating',
    )
    sort = django_filters.ChoiceFilter(
        choices=SORT_CHOICES,
        method='filter_sort',
        empty_label=None,
        label='Sort by',
    )

    class Meta:
        model = SkillOffer
        fields = []

    def search(self, queryset, name, value):
        text = value.strip().lower()
        queryset = queryset.annotate(title_lower=Lower('title'))
        return queryset.filter(title_lower__contains=text)

    def filter_min_rating(self, queryset, name, value):
        return queryset.filter(avg_rating__gte=int(value))

    def filter_sort(self, queryset, name, value):
        if value == 'rating':
            # no rating goes last
            best_first = F('avg_rating').desc(nulls_last=True)
            return queryset.order_by(best_first, '-reviews_count', '-created_at')
        if value == 'reviews':
            return queryset.order_by('-reviews_count', '-created_at')
        return queryset.order_by('-created_at')

