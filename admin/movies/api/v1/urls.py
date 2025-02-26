from django.urls import path

from .views import MoviesDetailApi, MovieSearch, MoviesListApi

urlpatterns = [
    path("movies/", MoviesListApi.as_view(), name="movie-list"),
    path("movies/<uuid:id>/", MoviesDetailApi.as_view(), name="movie-detail"),
    path("movies/search/", MovieSearch.as_view(), name="movie-search"),
]
