from django.contrib import admin

from .models import Category, Favorite, OfferRevision, SkillOffer


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name',)


@admin.register(SkillOffer)
class SkillOfferAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'category', 'level', 'format', 'status', 'created_at')
    list_filter = ('status', 'category', 'level', 'format')
    search_fields = ('title', 'author__username')
    list_select_related = ('author', 'category')
    autocomplete_fields = ('category',)
    raw_id_fields = ('author',)


@admin.register(OfferRevision)
class OfferRevisionAdmin(admin.ModelAdmin):
    list_display = ('offer', 'status', 'updated_at')
    list_filter = ('status',)
    list_select_related = ('offer',)
    raw_id_fields = ('offer',)


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('user', 'offer', 'created_at')
    list_select_related = ('user', 'offer')
    raw_id_fields = ('user', 'offer')

