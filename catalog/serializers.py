from rest_framework import serializers

from catalog.models import Author, Genre, Publisher


class AuthorSerializer(serializers.ModelSerializer):
    """Сериализатор для авторов."""
    books_writen = serializers.SerializerMethodField()
    books_translated = serializers.SerializerMethodField()

    class Meta:
        model = Author
        fields = [
            'id',
            'first_name',
            'last_name',
            'middle_name',
            'birth_date',
            'full_name',
            'pseudonym',
            'biography',
            'books_writen'
        ]
        read_only_fields = ['full_name']

    def get_books_writen(self, obj):
        if hasattr(obj, 'book_count'):
            return obj.book_count
        return obj.books.count()

    def get_books_translated(self, obj):
        if hasattr(obj, 'translations_count'):
            return obj.translations_count
        return obj.translations.count()


class GenreSerializer(serializers.ModelSerializer):
    """Сериализатор для жанров."""
    class Meta:
        model = Genre
        fields = ['id', 'name']


class PublisherSerializer(serializers.ModelSerializer):
    """Сериализатор для издательств."""
    class Meta:
        model = Publisher
        fields = ['id', 'name', 'description']
