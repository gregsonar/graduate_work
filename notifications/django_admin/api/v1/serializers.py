from rest_framework import serializers

from movies.models import Movie


class MovieSerializer(serializers.ModelSerializer):
    rating = serializers.FloatField(source='imdb_rating')
    genres = serializers.SlugRelatedField(
        many=True, read_only=True, slug_field='title'
    )
    actors = serializers.SlugRelatedField(
        many=True, read_only=True, slug_field='full_name'
    )
    directors = serializers.SlugRelatedField(
        many=True, read_only=True, slug_field='full_name'
    )
    writers = serializers.SlugRelatedField(
        many=True, read_only=True, slug_field='full_name'
    )

    class Meta:
        model = Movie
        fields = (
            'id',
            'title',
            'description',
            'creation_date',
            'rating',
            'type',
            'genres',
            'actors',
            'directors',
            'writers',
        )
