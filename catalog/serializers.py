from rest_framework import serializers

from catalog.models import Author, Genre, Publisher, Book, BookEdition


class AuthorSerializer(serializers.ModelSerializer):
    """Сериализатор для авторов."""
    books_written = serializers.SerializerMethodField()
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
            'books_written',
            'books_translated',
        ]
        read_only_fields = ['full_name']

    def get_books_written(self, obj):
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


class PublisherBriefSerializer(serializers.ModelSerializer):
    """Сериализатор для издательств без описания."""
    class Meta:
        model = Publisher
        fields = ['id', 'name']


class PublisherSerializer(PublisherBriefSerializer):
    """Полный сериализатор для издательства (с описанием)."""
    class Meta(PublisherBriefSerializer.Meta):
        fields = PublisherBriefSerializer.Meta.fields + ['description']


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


class BookEditionSerializer(serializers.ModelSerializer):
    """Сериализатор для конкретного издания произведения."""
    book = BookBriefSerializer(read_only=True)
    book_id = serializers.PrimaryKeyRelatedField(
        source='book',
        queryset=Book.objects.all(),
        write_only=True
    )
    publishers = PublisherBriefSerializer(read_only=True, many=True)
    publisher_ids = serializers.PrimaryKeyRelatedField(
        source='publishers',
        queryset=Publisher.objects.all(),
        write_only=True,
        many=True
    )
    translators = AuthorBriefSerializer(read_only=True, many=True)
    translator_ids = serializers.PrimaryKeyRelatedField(
        source='translators',
        queryset=Author.objects.all(),
        write_only=True,
        many=True
    )
    available_copies = serializers.IntegerField(read_only=True)

    class Meta:
        model = BookEdition
        fields = [
            'id',
            'title',
            'book',
            'book_id',
            'isbn',
            'publishers',
            'publisher_ids',
            'publication_year',
            'language',
            'translators',
            'translator_ids',
            'total_copies',
            'available_copies',
        ]

    def clean(self, validated_data):
        # Устанавливаем доступные копии равными общему количеству при создании
        validated_data['available_copies'] = validated_data.get('total_copies')
        return super().create(validated_data)
