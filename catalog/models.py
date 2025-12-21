from django.db import models

class Genre(models.Model):
    name = models.CharField(max_length=200, unique=True)
    spotify_genre_id = models.CharField(max_length=100, blank=True, null=True)
    description = models.TextField(blank=True)
    parent = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='subgenres')

    def __str__(self):
        return self.name


class Artist(models.Model):
    name = models.CharField(max_length=200)
    spotify_id = models.CharField(max_length=100, unique=True)
    genres = models.ManyToManyField(Genre, related_name='artists')

    def __str__(self):
        return self.name


class Track(models.Model):
    title = models.CharField(max_length=200)
    artist = models.ForeignKey(Artist, on_delete=models.CASCADE, related_name='tracks')
    spotify_id = models.CharField(max_length=100, unique=True, blank=True, null=True)
    spotify_url = models.URLField(max_length=500, blank=True, null=True)
    preview_url = models.URLField(max_length=500, blank=True, null=True)
    duration_ms = models.IntegerField(default=0)
    album_name = models.CharField(max_length=200, blank=True, null=True)
    album_image_url = models.URLField(max_length=500, blank=True, null=True)
    popularity = models.IntegerField(default=0)
    audio_features = models.JSONField(default=dict, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} - {self.artist.name}"