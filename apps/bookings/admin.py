from django.contrib import admin

from .models import LessonRequest


@admin.register(LessonRequest)
class LessonRequestAdmin(admin.ModelAdmin):
    list_display = ('offer', 'student', 'status', 'created_at')
    list_filter = ('status',)
    search_fields = ('offer__title', 'student__username')
    list_select_related = ('offer', 'student')
    raw_id_fields = ('offer', 'student')

