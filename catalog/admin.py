"""
Админ-панель для приложения catalog.
"""
from django.contrib import admin
from django.utils.html import format_html
from .models import Genre, Artist, Track


@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):
    list_display = ('name', 'track_count', 'is_popular', 'created_at')
    list_filter = ('is_popular', 'created_at')
    search_fields = ('name', 'lastfm_tag', 'description')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(Artist)
class ArtistAdmin(admin.ModelAdmin):
    list_display = ('name', 'lastfm_listeners', 'lastfm_playcount',
                    'is_popular', 'created_at')
    list_filter = ('is_popular', 'genres', 'created_at')
    search_fields = ('name', 'description')
    readonly_fields = ('created_at', 'updated_at', 'image_preview')
    filter_horizontal = ('genres',)

    def image_preview(self, obj):
        if obj.image_url:
            return format_html(
                '<img src="{}" style="max-height: 100px;" />',
                obj.image_url
            )
        return "Нет изображения"

    image_preview.short_description = "Превью"


@admin.register(Track)
class TrackAdmin(admin.ModelAdmin):
    list_display = ('title', 'artist', 'lastfm_playcount',
                    'lastfm_listeners', 'is_reference', 'created_at')
    list_filter = ('is_reference', 'artist', 'created_at')
    search_fields = ('title', 'artist__name', 'album')
    readonly_fields = ('created_at', 'updated_at', 'image_preview')
    raw_id_fields = ('artist',)

    def image_preview(self, obj):
        if obj.image_url:
            return format_html(
                '<img src="{}" style="max-height: 100px;" />',
                obj.image_url
            )
        return "Нет изображения"

    image_preview.short_description = "Превью"
