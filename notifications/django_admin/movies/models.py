import uuid

from django.core.validators import MinValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _


class Genre(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(_('Title'), max_length=255, unique=True)
    description = models.TextField(_('Description'), blank=True, null=True)
    updated_at = models.DateTimeField(
        auto_now=True, verbose_name=_('Updated at'), db_index=True
    )

    class Meta:
        verbose_name = _('Genre')
        verbose_name_plural = _('Genres')
        db_table = 'movies_genre'

    def __str__(self):
        return self.title


class Person(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    first_name = models.CharField(
        _('First name'), max_length=255, blank=True, null=True
    )
    last_name = models.CharField(_('Last name'), max_length=255)
    updated_at = models.DateTimeField(
        auto_now=True, verbose_name=_('Updated at'), db_index=True
    )

    @property
    def full_name(self):
        return '{} {}'.format(
            self.first_name or '', self.last_name or ''
        ).strip()

    class Meta:
        verbose_name = _('Person')
        verbose_name_plural = _('People')
        ordering = ('last_name',)
        db_table = 'movies_person'

    def __str__(self):
        return f'{self.last_name or ""} {self.first_name or ""}'


class MovieType(models.TextChoices):
    MOVIE = 'movie', _('Film')
    TV_SHOW = 'tv_show', _('Show')


class Movie(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(_('Title'), max_length=255)
    is_suspicious = models.BooleanField(_('Is suspicious'), default=False)
    description = models.TextField(_('Description'), blank=True, null=True)
    creation_date = models.DateField(
        _('Date of creation'), blank=True, null=True
    )
    certificate = models.TextField(_('Certificate'), blank=True, null=True)
    file_path = models.FileField(
        _('File'), upload_to='film_works/', blank=True, null=True
    )
    age_rating = models.FloatField(
        _('Rating'), validators=[MinValueValidator(0)], blank=True, null=True
    )
    imdb_rating = models.FloatField(
        _('IMDB rating'),
        validators=[MinValueValidator(0)],
        blank=False,
        null=False,
        default=0,
    )
    type = models.CharField(
        _('Type'),
        max_length=20,
        choices=MovieType.choices,
        null=False,
        blank=False,
        default=MovieType.MOVIE,
    )
    created = models.DateTimeField(
        _('Date of publication'), auto_now_add=True, db_index=True, null=True
    )
    updated_at = models.DateTimeField(
        auto_now=True, verbose_name=_('Updated at'), db_index=True
    )
    genres = models.ManyToManyField(
        Genre,
        related_name='movies',
        verbose_name=_('Genres'),
        db_table='movies_movie_genres',
    )
    directors = models.ManyToManyField(
        Person,
        related_name='movies_directed',
        verbose_name=_('Directors'),
        db_table='movies_movie_directors',
    )
    writers = models.ManyToManyField(
        Person,
        related_name='movies_written',
        verbose_name=_('Writers'),
        db_table='movies_movie_writers',
    )
    actors = models.ManyToManyField(
        Person,
        related_name='movies_acted',
        verbose_name=_('Actors'),
        db_table='movies_movie_actors',
    )

    class Meta:
        verbose_name = _('Movie')
        verbose_name_plural = _('Movies')
        ordering = ('-title',)
        db_table = 'movies_movie'

    def __str__(self):
        return self.title
