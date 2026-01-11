"""
Модели данных для приложения catalog.
"""
import json
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.urls import reverse
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.conf import settings


class Genre(models.Model):
    """
    Модель музыкального жанра/тега из Last.fm.
    """
    name = models.CharField(
        max_length=100,
        verbose_name="Название жанра",
        unique=True
    )
    description = models.TextField(
        verbose_name="Описание жанра",
        blank=True,
        null=True
    )
    lastfm_tag = models.CharField(
        max_length=100,
        verbose_name="Тег в Last.fm",
        blank=True,
        null=True,
        help_text="Соответствующий тег в Last.fm API"
    )
    lastfm_url = models.URLField(
        verbose_name="Страница в Last.fm",
        blank=True,
        null=True
    )
    track_count = models.IntegerField(
        verbose_name="Количество треков",
        default=0
    )
    is_popular = models.BooleanField(
        verbose_name="Популярный жанр",
        default=False
    )
    created_at = models.DateTimeField(
        verbose_name="Дата создания",
        auto_now_add=True
    )
    updated_at = models.DateTimeField(
        verbose_name="Дата обновления",
        auto_now=True
    )

    class Meta:
        verbose_name = "Жанр"
        verbose_name_plural = "Жанры"
        ordering = ['-track_count', 'name']

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('genre_detail', kwargs={'pk': self.pk})

    def save(self, *args, **kwargs):
        if not self.lastfm_tag:
            self.lastfm_tag = self.name.lower()
        super().save(*args, **kwargs)


class Artist(models.Model):
    """
    Модель музыкального исполнителя.
    """
    name = models.CharField(
        max_length=200,
        verbose_name="Имя исполнителя"
    )
    lastfm_url = models.URLField(
        verbose_name="Страница в Last.fm",
        blank=True,
        null=True
    )
    lastfm_listeners = models.IntegerField(
        verbose_name="Количество слушателей",
        default=0
    )
    lastfm_playcount = models.IntegerField(
        verbose_name="Количество прослушиваний",
        default=0
    )
    description = models.TextField(
        verbose_name="Описание исполнителя",
        blank=True,
        null=True
    )
    image_url = models.URLField(
        verbose_name="URL изображения",
        blank=True,
        null=True,
        max_length=500
    )
    genres = models.ManyToManyField(
        Genre,
        verbose_name="Жанры",
        related_name="artists",
        blank=True
    )
    is_popular = models.BooleanField(
        verbose_name="Популярный исполнитель",
        default=False
    )
    created_at = models.DateTimeField(
        verbose_name="Дата добавления",
        auto_now_add=True
    )
    updated_at = models.DateTimeField(
        verbose_name="Дата обновления",
        auto_now=True
    )

    class Meta:
        verbose_name = "Исполнитель"
        verbose_name_plural = "Исполнители"
        ordering = ['-lastfm_listeners', 'name']
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['lastfm_listeners']),
        ]

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('artist_detail', kwargs={'pk': self.pk})

    def update_popularity(self):
        """Обновление статуса популярности исполнителя."""
        self.is_popular = self.lastfm_listeners > 100000
        self.save()

    @property
    def top_genres(self):
        """Топ 3 жанра исполнителя."""
        return self.genres.all()[:3]


class Track(models.Model):
    """
    Модель музыкального трека.
    """
    title = models.CharField(
        max_length=200,
        verbose_name="Название трека"
    )
    artist = models.ForeignKey(
        Artist,
        on_delete=models.CASCADE,
        verbose_name="Исполнитель",
        related_name="tracks"
    )
    lastfm_url = models.URLField(
        verbose_name="Страница в Last.fm",
        blank=True,
        null=True
    )
    lastfm_listeners = models.IntegerField(
        verbose_name="Количество слушателей",
        default=0
    )
    lastfm_playcount = models.IntegerField(
        verbose_name="Количество прослушиваний",
        default=0
    )
    duration = models.IntegerField(
        verbose_name="Продолжительность (секунды)",
        blank=True,
        null=True
    )
    album = models.CharField(
        max_length=200,
        verbose_name="Альбом",
        blank=True,
        null=True
    )
    tags_json = models.TextField(
        verbose_name="Теги (JSON)",
        blank=True,
        null=True,
        help_text="Теги и жанры трека в формате JSON"
    )
    lastfm_data = models.TextField(
        verbose_name="Данные Last.fm (JSON)",
        blank=True,
        null=True,
        help_text="Полные данные из Last.fm API в формате JSON"
    )
    image_url = models.URLField(
        verbose_name="URL изображения",
        blank=True,
        null=True,
        max_length=500
    )
    is_reference = models.BooleanField(
        verbose_name="Референс-трек",
        default=False,
        help_text="Использовать как референс для анализа жанра"
    )
    created_at = models.DateTimeField(
        verbose_name="Дата добавления",
        auto_now_add=True
    )
    updated_at = models.DateTimeField(
        verbose_name="Дата обновления",
        auto_now=True
    )

    class Meta:
        verbose_name = "Трек"
        verbose_name_plural = "Треки"
        ordering = ['-lastfm_playcount', 'title']
        indexes = [
            models.Index(fields=['title']),
            models.Index(fields=['lastfm_playcount']),
            models.Index(fields=['is_reference']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['title', 'artist'],
                name='unique_track_per_artist'
            )
        ]

    def __str__(self):
        return f"{self.title} - {self.artist.name}"

    def get_absolute_url(self):
        return reverse('track_detail', kwargs={'pk': self.pk})

    def get_lastfm_data(self):
        """Проверяет, есть ли данные из Last.fm."""
        return bool(self.lastfm_listeners or self.lastfm_playcount)

    @property
    def formatted_duration(self):
        """Форматирует длительность трека."""
        if not self.duration:
            return "Неизвестно"

        minutes = self.duration // 60
        seconds = self.duration % 60
        return f"{minutes}:{seconds:02d}"

    @property
    def tags(self):
        """Получение тегов как списка."""
        if self.tags_json:
            try:
                return json.loads(self.tags_json)
            except (json.JSONDecodeError, TypeError):
                return []
        return []

    @tags.setter
    def tags(self, value):
        """Установка тегов."""
        if isinstance(value, list):
            self.tags_json = json.dumps(value, ensure_ascii=False)
        else:
            self.tags_json = json.dumps([], ensure_ascii=False)

    def get_lastfm_data(self):
        """Получение данных Last.fm как словаря."""
        if self.lastfm_data:
            try:
                return json.loads(self.lastfm_data)
            except (json.JSONDecodeError, TypeError):
                return {}
        return {}

    def set_lastfm_data(self, value):
        """Сохранение данных Last.fm."""
        if isinstance(value, dict):
            self.lastfm_data = json.dumps(value, ensure_ascii=False)
        else:
            self.lastfm_data = json.dumps({}, ensure_ascii=False)

    def calculate_popularity_score(self):
        """Расчет рейтинга популярности трека."""
        if self.lastfm_playcount > 0 and self.lastfm_listeners > 0:
            normalized_playcount = min(self.lastfm_playcount / 1000000, 1.0)
            normalized_listeners = min(self.lastfm_listeners / 500000, 1.0)
            return 0.7 * normalized_playcount + 0.3 * normalized_listeners
        return 0.0

    def link_genres_from_tags(self):
        """Связывание трека с жанрами на основе тегов."""
        if not self.tags:
            return

        for tag_name in self.tags[:5]:
            genre, created = Genre.objects.get_or_create(
                name=tag_name.title(),
                defaults={
                    'lastfm_tag': tag_name.lower(),
                    'description': f'Жанр на основе тега Last.fm: {tag_name}'
                }
            )
            if genre not in self.artist.genres.all():
                self.artist.genres.add(genre)


class Favorite(models.Model):
    """Модель для хранения избранных элементов пользователя"""
    ITEM_TYPES = [
        ('genre', 'Жанр'),
        ('track', 'Трек'),
        ('artist', 'Исполнитель'),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name="Пользователь",
        related_name="favorites"
    )

    item_type = models.CharField(
        max_length=20,
        choices=ITEM_TYPES,
        verbose_name="Тип элемента",
        default='genre'
    )
    item_id = models.CharField(
        max_length=255,
        verbose_name="ID элемента",
        help_text="ID жанра, трека или исполнителя"
    )

    created_at = models.DateTimeField(
        verbose_name="Дата добавления",
        auto_now_add=True
    )

    class Meta:
        verbose_name = "Избранное"
        verbose_name_plural = "Избранное"
        unique_together = ['user', 'item_type', 'item_id']
        ordering = ['-created_at']

    def __str__(self):
        item_name = self.get_item_name()
        return f"{self.user.username} → {self.get_item_type_display()}: {item_name}"

    def get_item_name(self):
        """Получение названия связанного элемента."""
        if self.item_type == 'genre':
            genre = Genre.objects.filter(id=self.item_id).first()
            return genre.name if genre else f"Жанр #{self.item_id}"
        elif self.item_type == 'track':
            track = Track.objects.filter(id=self.item_id).first()
            return track.title if track else f"Трек #{self.item_id}"
        elif self.item_type == 'artist':
            artist = Artist.objects.filter(id=self.item_id).first()
            return artist.name if artist else f"Исполнитель #{self.item_id}"
        return f"Элемент #{self.item_id}"

    def get_item(self):
        """Получение связанного объекта."""
        if self.item_type == 'genre':
            return Genre.objects.filter(id=self.item_id).first()
        elif self.item_type == 'track':
            return Track.objects.filter(id=self.item_id).first()
        elif self.item_type == 'artist':
            return Artist.objects.filter(id=self.item_id).first()
        return None


class UserProfile(models.Model):
    """Расширенный профиль пользователя."""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    bio = models.TextField(blank=True, null=True, max_length=500)
    favorite_genres = models.ManyToManyField(Genre, blank=True)
    lastfm_username = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Профиль: {self.user.username}"

    @receiver(post_save, sender=User)
    def create_user_profile(sender, instance, created, **kwargs):
        if created:
            UserProfile.objects.create(user=instance)

    @receiver(post_save, sender=User)
    def save_user_profile(sender, instance, **kwargs):
        instance.profile.save()


@receiver(post_save, sender=User)
def send_welcome_email(sender, instance, created, **kwargs):
    """Отправка приветственного письма после регистрации."""
    if created and instance.email:
        try:
            send_mail(
                subject='Добро пожаловать в Genrefy!',
                message=f'Привет, {instance.username}!\n\n'
                        f'Спасибо за регистрацию в Genrefy!\n'
                        f'Теперь вы можете:\n'
                        f'- Добавлять жанры в избранное\n'
                        f'- Получать рекомендации\n'
                        f'- Создавать свои коллекции\n\n'
                        f'Начните исследовать музыку прямо сейчас!\n\n'
                        f'С уважением,\nКоманда Genrefy',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[instance.email],
                fail_silently=True,
            )
        except:
            pass
