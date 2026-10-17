from django.contrib import admin

from .models import Review


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('offer', 'author', 'rating', 'created_at')
    list_filter = ('rating',)
    search_fields = ('offer__title', 'author__username', 'text')
    list_select_related = ('offer', 'author')
    raw_id_fields = ('lesson_request', 'offer', 'author')

