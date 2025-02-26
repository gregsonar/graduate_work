from elasticsearch_dsl import Q, Search
from elasticsearch_dsl.query import MatchAll, MultiMatch, Nested, Term
from rest_framework.response import Response
from rest_framework.views import APIView

from django.conf import settings
from django.core.paginator import Paginator
from django.db.models import Prefetch
from django.http import Http404, JsonResponse
from django.views.generic.detail import BaseDetailView
from django.views.generic.list import BaseListView

from ...models import FilmWork, PersonFilmWork
from .serializers import MovieSerializer


class MoviesApiMixin:
    model = FilmWork
    http_method_names = ["get"]

    def get_queryset(self):
        return FilmWork.objects.prefetch_related(
            "genres",
            Prefetch(
                "personfilmwork_set",
                queryset=PersonFilmWork.objects.select_related("person"),
            ),
        )

    def render_to_response(self, context, **response_kwargs):
        return JsonResponse(context)


class MoviesListApi(MoviesApiMixin, BaseListView):
    paginate_by = 50

    def get_context_data(self, **kwargs):
        queryset = self.get_queryset()
        paginator = Paginator(queryset, self.paginate_by)
        page = self.request.GET.get("page")

        if page == "last":
            page = paginator.num_pages

        try:
            page_obj = paginator.page(page)
        except:
            page_obj = paginator.page(1)

        serializer = MovieSerializer(page_obj.object_list, many=True)

        return {
            "count": paginator.count,
            "total_pages": paginator.num_pages,
            "prev": (
                page_obj.previous_page_number() if page_obj.has_previous() else None
            ),
            "next": page_obj.next_page_number() if page_obj.has_next() else None,
            "results": serializer.data,
        }


class MoviesDetailApi(MoviesApiMixin, BaseDetailView):
    pk_url_kwarg = "id"

    def get_object(self, queryset=None):
        if queryset is None:
            queryset = self.get_queryset()

        pk = self.kwargs.get(self.pk_url_kwarg)
        if pk is None:
            raise Http404("No UUID given")

        try:
            obj = queryset.get(pk=pk)
        except queryset.model.DoesNotExist:
            raise Http404("Film not found")

        return obj

    def get_context_data(self, **kwargs):
        film_work = self.get_object()
        serializer = MovieSerializer(film_work)
        return serializer.data


class MovieSearch(APIView):
    def get(self, request):
        s = Search(using=settings.ELASTICSEARCH_DSL["default"], index="movies")

        # Получаем параметры запроса
        query = request.GET.get("query")
        actor = request.GET.get("actor")
        writer = request.GET.get("writer")
        director = request.GET.get("director")
        genre = request.GET.get("genre")

        if query:
            q = MultiMatch(
                query=query,
                fields=[
                    "actors_names",
                    "writers_names",
                    "title",
                    "description",
                    "genres",
                ],
                fuzziness="auto",
            )
            s = s.query(q)
        elif actor:
            q = Nested(path="actors", query=Q("match", actors__name=actor))
            s = s.query(q)
        elif writer:
            q = Nested(path="writers", query=Q("match", writers__name=writer))
            s = s.query(q)
        elif director:
            q = Nested(path="directors", query=Q("match", directors__name=director))
            s = s.query(q)
        elif genre:
            s = s.filter("term", genres=genre)
        else:
            s = s.query(MatchAll())

        response = s.execute()

        results = [
            {
                "id": hit.id,
                "title": hit.title,
                "description": hit.description,
                "imdb_rating": hit.imdb_rating,
                "genres": hit.genres,
                "actors": hit.actors_names,
                "writers": hit.writers_names,
                "directors": hit.directors_names,
            }
            for hit in response
        ]

        return Response({"count": response.hits.total.value, "results": results})


class MovieDetail(APIView):
    def get(self, request, movie_id):
        s = Search(using=settings.ELASTICSEARCH_DSL["default"], index="movies")
        q = Term(id=movie_id)
        response = s.query(q).execute()

        if response.hits.total.value == 0:
            return Response({"error": "Movie not found"}, status=404)

        hit = response.hits[0]
        result = {
            "id": hit.id,
            "title": hit.title,
            "description": hit.description,
            "imdb_rating": hit.imdb_rating,
            "genres": hit.genres,
            "actors": hit.actors_names,
            "writers": hit.writers_names,
            "directors": hit.directors_names,
        }

        return Response(result)


class GenreAggregation(APIView):
    def get(self, request):
        s = Search(using=settings.ELASTICSEARCH_DSL["default"], index="movies")
        s.aggs.bucket("genres", "terms", field="genres", size=100)
        response = s.execute()

        genres = [
            {"genre": bucket.key, "count": bucket.doc_count}
            for bucket in response.aggregations.genres.buckets
        ]

        return Response(genres)
