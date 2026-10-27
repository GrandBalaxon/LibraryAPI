from django.core.exceptions import ValidationError
from stdnum import isbn
from stdnum.exceptions import InvalidLength, InvalidChecksum, InvalidFormat, InvalidComponent

_ISBN_ERROR_MESSAGES = {
    InvalidLength: 'Неверная длина ISBN. ISBN должен состоять из 10 или 13 цифр.',
    InvalidChecksum: (
        'Неверный ISBN. Последняя цифра (контрольная сумма) '
        'не совпадает с остальными. Проверьте введенные данные.'
    ),
    InvalidFormat: (
        'Неверный формат ISBN. Разрешены только цифры, дефисы и пробелы. '
        'Убедитесь, что нет лишних букв или символов.'
    ),
    InvalidComponent: (
        'Некорректная составная часть ISBN. '
        'Проверьте правильность префикса (например, 978 или 979) и региона.'
    ),
}


def validate_isbn(value: str | None) -> str | None:
    """
    Валидирует и нормализует ISBN: возвращает ISBN-13 с дефисами
    либо само значение, если оно пустое.
    При ошибке поднимает ValidationError с plain-строкой — это позволяет и модели, и DRF обработать её одинаково.
    """
    if not value:
        return value

    try:
        # Валидируем и получаем компактный вид
        compact_isbn = isbn.validate(value)
        # Форматируем: приводим к ISBN-13 и добавляем правильные дефисы
        return isbn.format(compact_isbn, convert=True)

    except (InvalidLength, InvalidChecksum, InvalidFormat, InvalidComponent) as exc:
        raise ValidationError(str(_ISBN_ERROR_MESSAGES[type(exc)])) from exc
