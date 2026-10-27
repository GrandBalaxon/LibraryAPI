from rest_framework import serializers

from catalog.models import Author, Genre, Publisher, Work, Edition, BookCopy
from catalog.validators import validate_isbn as isbn_validator


class AuthorSerializer(serializers.ModelSerializer):
    """Сериализатор для авторов."""
    works_written = serializers.SerializerMethodField()
    works_translated = serializers.SerializerMethodField()

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
            'works_written',
            'works_translated',
        ]
        read_only_fields = ['full_name']

    def get_works_written(self, obj) -> int:
        if hasattr(obj, 'works_count'):
            return obj.works_count
        return obj.works.count()

    def get_works_translated(self, obj) -> int:
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


class WorkBriefSerializer(serializers.ModelSerializer):
    """Краткая информация о произведении."""
    authors = AuthorBriefSerializer(many=True, read_only=True)
    genres = GenreSerializer(many=True, read_only=True)

    class Meta:
        model = Work
        fields = [
            'id',
            'original_title',
            'original_language',
            'writing_year',
            'authors',
            'genres',
            'description',
        ]


class WorkSerializer(WorkBriefSerializer):
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

    class Meta(WorkBriefSerializer.Meta):
        fields = WorkBriefSerializer.Meta.fields + ['author_ids', 'genre_ids']


class BookCopyBriefSerializer(serializers.ModelSerializer):
    """Краткая информация об экземпляре (для вложения в Edition)."""

    class Meta:
        model = BookCopy
        fields = ['id', 'inventory_number', 'status', 'condition', 'location']


class EditionSerializer(serializers.ModelSerializer):
    """Сериализатор для конкретного издания произведения."""
    work = WorkBriefSerializer(read_only=True)
    work_id = serializers.PrimaryKeyRelatedField(
        source='work',
        queryset=Work.objects.all(),
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
    copies = BookCopyBriefSerializer(many=True, read_only=True)
    copies_count = serializers.SerializerMethodField()
    available_copies_count = serializers.SerializerMethodField()

    class Meta:
        model = Edition
        fields = [
            'id',
            'work',
            'work_id',
            'title',
            'isbn',
            'publishers',
            'publisher_ids',
            'publication_year',
            'language',
            'translators',
            'translator_ids',
            'pages',
            'copies',
            'copies_count',
            'available_copies_count',
        ]

    def get_copies_count(self, obj) -> int:
        """Подсчёт всех экземпляров."""
        # Если ViewSet сделал annotate (список), берем готовое число из базы
        if hasattr(obj, 'total_copies_count'):
            return obj.total_copies_count
        # Если объект запрашивается в одиночку (retrieve), считаем вручную
        return obj.copies.count()

    def get_available_copies_count(self, obj) -> int:
        """Подсчёт экземпляров, у которых статус AVAILABLE."""
        # Если ViewSet сделал annotate (список), берем готовое число из базы
        if hasattr(obj, 'available_copies_count'):
            return obj.available_copies_count
        # Если объект запрашивается в одиночку (retrieve), считаем вручную
        return obj.copies.filter(status=BookCopy.Status.AVAILABLE).count()

    def validate_isbn(self, value: str | None) -> str | None:
        """Валидация и форматирование ISBN на уровне API."""
        return isbn_validator(value)

    def update(self, instance: Edition, validated_data: dict) -> Edition:
        """Запрещаем менять произведение или ISBN, если у издания уже есть копии."""
        has_copies = instance.copies.exists()

        if has_copies:
            # Проверка на изменение Work
            if 'work' in validated_data and validated_data['work'] != instance.work:
                raise serializers.ValidationError(
                    {'work_id': ['Нельзя изменить произведение у издания, которое уже поступило в библиотеку.']}
                )
            # Проверка на изменение ISBN
            if 'isbn' in validated_data and validated_data['isbn'] != instance.isbn:
                raise serializers.ValidationError(
                    {'isbn': ['Нельзя изменить ISBN, так как на обложках экземпляров напечатан старый номер.']}
                )

        return super().update(instance, validated_data)


class BookCopySerializer(serializers.ModelSerializer):
    """Сериализатор для управления конкретными экземплярами книг."""
    edition_title = serializers.CharField(source='edition.title', read_only=True)
    work_title = serializers.CharField(source='edition.work.original_title', read_only=True)

    class Meta:
        model = BookCopy
        fields = [
            'id',
            'edition',
            'edition_title',
            'work_title',
            'inventory_number',
            'status',
            'condition',
            'location',
            'notes',
        ]
        extra_kwargs = {
            'inventory_number': {'required': False},
        }

    def create(self, validated_data: dict) -> BookCopy:
        """При создании, если нет инвентарного номера, генерируем его."""
        if not validated_data.get('inventory_number'):
            edition = validated_data['edition']
            validated_data['inventory_number'] = edition.generate_next_inventory_number()

        return super().create(validated_data)


class CopyCountSerializer(serializers.Serializer):
    """Сериализатор для приёма количества копий."""
    count = serializers.IntegerField(min_value=1, help_text='Количество копий')
