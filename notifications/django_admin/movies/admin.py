from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from .models import Movie, Genre, Person


class UsersInline(admin.TabularInline):
    model = Person
    fields = ('first_name', 'last_name')
    readonly_fields = ('first_name', 'last_name')


class MoviesInline(admin.TabularInline):
    model = Movie
    fields = ('title',)
    readonly_fields = ('title',)


@admin.register(Movie)
class MovieAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'is_suspicious',
        'get_genres',
        'get_actors',
        'get_directors',
        'get_writers',
        'type',
        'creation_date',
        'updated_at',
    )
    search_fields = ('title', 'description')
    list_filter = ('genres', 'is_suspicious')
    list_prefetch_related = ('actors', 'directors', 'writers', 'genres')

    def get_queryset(self, request):
        queryset = (
            super(MovieAdmin, self)
            .get_queryset(request)
            .prefetch_related(*self.list_prefetch_related)
        )
        return queryset

    def get_genres(self, obj):
        return ','.join([genre.title for genre in obj.genres.all()])

    def get_actors(self, obj):
        return ','.join([str(actor) for actor in obj.actors.all()])

    def get_writers(self, obj):
        return ','.join([str(writer) for writer in obj.writers.all()])

    def get_directors(self, obj):
        return ','.join([str(director) for director in obj.directors.all()])

    get_genres.short_description = _('Genres')
    get_actors.short_description = _('Actors')
    get_directors.short_description = _('Directors')
    get_writers.short_description = _('Writers')


@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):
    list_display = ('title', 'get_films_amount', 'updated_at')
    search_fields = ('title',)
    empty_value_display = _('-empty-')
    fields = ('title', 'description')

    def get_queryset(self, request):
        queryset = (
            super(GenreAdmin, self)
            .get_queryset(request)
            .prefetch_related('movies')
        )
        return queryset

    def get_films_amount(self, obj):
        return obj.movies.count()

    get_films_amount.short_description = _('Movies amount')


@admin.register(Person)
class PersonAdmin(admin.ModelAdmin):
    list_display = (
        'last_name',
        'first_name',
        'get_acted',
        'get_directed',
        'get_written',
        'updated_at'
    )
    search_fields = ('first_name', 'last_name')
    empty_value_display = _('-empty-')

    list_prefetch_related = (
        'movies_directed',
        'movies_written',
        'movies_acted',
    )

    def get_queryset(self, request):
        queryset = (
            super(PersonAdmin, self)
            .get_queryset(request)
            .prefetch_related(*self.list_prefetch_related)
        )
        return queryset

    def get_acted(self, obj):
        return ', '.join([movie.title for movie in obj.movies_acted.all()])

    def get_directed(self, obj):
        return ', '.join([movie.title for movie in obj.movies_directed.all()])

    def get_written(self, obj):
        return ', '.join([movie.title for movie in obj.movies_written.all()])

    get_acted.short_description = _('Acted in')
    get_directed.short_description = _('Directed')
    get_written.short_description = _('Wrote script to')
