from django import forms
from .models import Track, Artist, Genre, Favorite


class SearchForm(forms.Form):
    """
    Форма для поиска треков и артистов через Last.fm API
    """
    SEARCH_TYPE_CHOICES = [
        ('track', 'Трек'),
        ('artist', 'Артист'),
    ]

    query = forms.CharField(
        label='Поиск',
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите название трека или артиста...'
        })
    )

    search_type = forms.ChoiceField(
        label='Тип поиска',
        choices=SEARCH_TYPE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'}),
        initial='track'
    )

    def clean_query(self):
        query = self.cleaned_data['query'].strip()
        if len(query) < 2:
            raise forms.ValidationError("Введите минимум 2 символа для поиска")
        return query


class AddTrackFromLastFMForm(forms.Form):
    track_name = forms.CharField(
        label='Название трека',
        max_length=200,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    artist_name = forms.CharField(
        label='Исполнитель',
        max_length=200,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    genre = forms.ModelChoiceField(
        queryset=Genre.objects.all(),
        label='Основной жанр (опционально)',
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    tags = forms.CharField(
        label='Теги через запятую (опционально)',
        max_length=500,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'rock, alternative, indie'})
    )

    def clean(self):
        cleaned_data = super().clean()
        track_name = cleaned_data.get('track_name')
        artist_name = cleaned_data.get('artist_name')

        if track_name and artist_name:
            if Track.objects.filter(title__iexact=track_name, artist__name__iexact=artist_name).exists():
                raise forms.ValidationError(
                    f'Трек "{track_name}" исполнителя "{artist_name}" уже существует в базе.'
                )

        return cleaned_data


class FavoriteForm(forms.Form):
    """
    Форма для добавления трека в избранное
    """
    track_id = forms.CharField(widget=forms.HiddenInput())
    artist_id = forms.CharField(widget=forms.HiddenInput())
    track_name = forms.CharField(widget=forms.HiddenInput())
    artist_name = forms.CharField(widget=forms.HiddenInput())


class GenreAnalysisForm(forms.Form):
    """
    Форма для выбора параметров анализа жанров
    """
    TIME_PERIOD_CHOICES = [
        ('7day', 'За неделю'),
        ('1month', 'За месяц'),
        ('3month', 'За 3 месяца'),
        ('6month', 'За полгода'),
        ('12month', 'За год'),
        ('overall', 'За всё время'),
    ]

    time_period = forms.ChoiceField(
        label='Период анализа',
        choices=TIME_PERIOD_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'}),
        initial='1month'
    )

    limit = forms.IntegerField(
        label='Количество жанров',
        min_value=1,
        max_value=50,
        initial=10,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )

    def clean_limit(self):
        limit = self.cleaned_data['limit']
        if limit < 1 or limit > 50:
            raise forms.ValidationError("Количество жанров должно быть от 1 до 50")
        return limit


class SaveTrackFromSearchForm(forms.Form):
    """
    Форма для сохранения найденного трека в базу.
    """
    track_name = forms.CharField(widget=forms.HiddenInput())
    artist_name = forms.CharField(widget=forms.HiddenInput())

    genre = forms.ModelChoiceField(
        label='Основной жанр',
        queryset=Genre.objects.all(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
