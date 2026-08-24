from drf_spectacular.utils import extend_schema, extend_schema_view


def standard_viewset_schema(tags):
    """Декоратор, добавляющий стандартные summaries и теги для ViewSet."""
    def decorator(viewset_class):
        # Применяем extend_schema с тегами
        viewset_class = extend_schema(tags=tags)(viewset_class)
        # Применяем extend_schema_view со стандартными summaries
        viewset_class = extend_schema_view(
            list=extend_schema(summary='Список'),
            create=extend_schema(summary='Создание'),
            retrieve=extend_schema(summary='Детали'),
            update=extend_schema(summary='Обновление'),
            partial_update=extend_schema(summary='Частичное обновление'),
            destroy=extend_schema(summary='Удаление')
        )(viewset_class)
        return viewset_class
    return decorator
