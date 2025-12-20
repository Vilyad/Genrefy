from django.contrib import admin
from .models import Genre, Artist, Track

@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):
    list_display = ('name', 'parent')
    search_fields = ('name',)

@admin.register(Artist)
class ArtistAdmin(admin.ModelAdmin):
    list_display = ('name', 'spotify_id')
    search_fields = ('name',)
    filter_horizontal = ('genres',)

@admin.register(Track)
class TrackAdmin(admin.ModelAdmin):
    list_display = ('title', 'artist', 'spotify_id')
    list_filter = ('artist__genres',)
    search_fields = ('title', 'artist__name')