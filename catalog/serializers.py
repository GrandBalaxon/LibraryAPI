from rest_framework import serializers
from stdnum import isbn
from stdnum.exceptions import InvalidLength, InvalidChecksum, InvalidFormat, InvalidComponent

from catalog.models import Author, Genre, Publisher, Work, Edition, BookCopy


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
    copies_count = serializers.IntegerField(source='copies.count', read_only=True)
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

    def get_available_copies_count(self, obj) -> int:
        """Подсчёт экземпляров, у которых статус AVAILABLE."""
        return obj.copies.filter(status=BookCopy.Status.AVAILABLE).count()

    def validate_isbn(self, value: str | None) -> str | None:
        """Валидация ISBN на уровне API."""
        if not value:
            return value

        try:
            # Валидируем и получаем компактный вид
            compact_isbn = isbn.validate(value)
            # Форматируем: приводим к ISBN-13 и добавляем правильные дефисы
            return isbn.format(compact_isbn, convert=True)

        except InvalidLength:
            raise serializers.ValidationError("Неверная длина ISBN. ISBN должен состоять из 10 или 13 цифр.")
        except InvalidChecksum:
            raise serializers.ValidationError(
                "Неверный ISBN. Последняя цифра (контрольная сумма) "
                "не совпадает с остальными. Проверьте введенные данные."
            )
        except InvalidFormat:
            raise serializers.ValidationError(
                "Неверный формат ISBN. Разрешены только цифры, дефисы и пробелы. "
                "Убедитесь, что нет лишних букв или символов."
            )
        except InvalidComponent:
            raise serializers.ValidationError(
                "Некорректная составная часть ISBN. "
                "Проверьте правильность префикса (например, 978 или 979) и региона."
            )


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


class CopyCountSerializer(serializers.Serializer):
    """Сериализатор для приёма количества копий."""
    count = serializers.IntegerField(min_value=1, help_text='Количество копий')
