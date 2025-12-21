from django import forms
from .models import Track, Artist, Genre

class AddTrackForm(forms.Form):
    spotify_url = forms.CharField(
        label='Spotify URL или ID трека',
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'https://open.spotify.com/track/... или spotify:track:...'
        })
    )

    genre = forms.ModelChoiceField(
        label='Жанр',
        queryset=Genre.objects.all(),
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    def clean_spotify_url(self):
        url = self.cleaned_data['spotify_url']
        if not url:
            raise forms.ValidationError("Введите Spotify URL или ID трека")
        return url

class SearchTrackForm(forms.Form):
    query = forms.CharField(
        label='Поиск трека',
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Название трека или артиста...'
        })
    )

    def clean_query(self):
        query = self.cleaned_data['query']
        if len(query) < 2:
            raise forms.ValidationError("Введите минимум 2 символа для поиска")
        return query