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
    """
    Форма для добавления трека из Last.fm в базу данных
    """
    track_name = forms.CharField(
        label='Название трека',
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите название трека...'
        })
    )

    artist_name = forms.CharField(
        label='Исполнитель',
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите имя исполнителя...'
        })
    )

    genre = forms.ModelChoiceField(
        label='Жанр',
        queryset=Genre.objects.all(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    tags = forms.CharField(
        label='Теги (через запятую)',
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'rock, alternative, indie...'
        })
    )

    def clean(self):
        cleaned_data = super().clean()
        track_name = cleaned_data.get('track_name')
        artist_name = cleaned_data.get('artist_name')

        if not track_name or not artist_name:
            raise forms.ValidationError("Введите название трека и исполнителя")

        if Track.objects.filter(name=track_name, artist__name=artist_name).exists():
            raise forms.ValidationError("Этот трек уже есть в базе данных")

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
