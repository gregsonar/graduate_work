from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import MoviesListView


router = DefaultRouter()
router.register('movies', MoviesListView, basename='movies')

urlpatterns = [path('', include(router.urls))]
