from rest_framework import serializers

from catalog.models import Author, Genre, Publisher, Book


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


class AuthorBriefSerializer(serializers.ModelSerializer):
    """Краткая информация об авторе для вложенных объектов."""
    class Meta:
        model = Author
        fields = ['id', 'full_name', 'pseudonym']


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


class BookBriefSerializer(serializers.ModelSerializer):
    """Краткая информация о произведении (базовый для полного)."""
    authors = AuthorBriefSerializer(many=True, read_only=True)
    genres = GenreSerializer(many=True, read_only=True)

    class Meta:
        model = Book
        fields = [
            'id',
            'title',
            'original_title',
            'original_language',
            'writing_year',
            'authors',
            'genres',
            'description',
        ]


class BookSerializer(BookBriefSerializer):
    """Полный сериализатор произведения с полями для записи связей."""
    author_ids = serializers.PrimaryKeyRelatedField(
        source='authors',
        queryset=Author.objects.all(),
        many=True,
        write_only=True
    )
    genre_ids = serializers.PrimaryKeyRelatedField(
        source='genres',
        queryset=Genre.objects.all(),
        many=True,
        write_only=True
    )

    class Meta(BookBriefSerializer.Meta):
        fields = BookBriefSerializer.Meta.fields + ['author_ids', 'genre_ids']



