from rest_framework import serializers
from ...models import FilmWork, Roles


class MovieSerializer(serializers.ModelSerializer):
    genres = serializers.SlugRelatedField(many=True, slug_field='name', read_only=True)
    actors = serializers.SerializerMethodField()
    directors = serializers.SerializerMethodField()
    writers = serializers.SerializerMethodField()
    rating = serializers.FloatField(allow_null=True)

    class Meta:
        model = FilmWork
        fields = [
            'id', 'title', 'description',
            'creation_date', 'rating', 'type',
            'genres', 'actors', 'directors',
            'writers'
        ]

    def get_person_names(self, obj, role):
        return [p.person.full_name for p in obj.personfilmwork_set.filter(role=role)]

    def get_actors(self, obj):
        return self.get_person_names(obj, Roles.ACTOR)

    def get_directors(self, obj):
        return self.get_person_names(obj, Roles.DIRECTOR)

    def get_writers(self, obj):
        return self.get_person_names(obj, Roles.WRITER)

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        ret['rating'] = float(ret['rating']) if ret['rating'] is not None else 0
        ret['creation_date'] = ret['creation_date'].isoformat() if ret['creation_date'] is not None else None
        return ret
