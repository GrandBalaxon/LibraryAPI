# LibraryAPI — REST API для управления библиотекой

![Python](https://img.shields.io/badge/python-3.14-blue.svg)
![Django](https://img.shields.io/badge/django-6.1-green.svg)
![DRF](https://img.shields.io/badge/django%20rest%20framework-3.18-red.svg)
![PostgreSQL](https://img.shields.io/badge/postgresql-16-blue.svg)
![Docker](https://img.shields.io/badge/docker-compose-blue.svg)
![OpenAPI](https://img.shields.io/badge/OpenAPI-3.0-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

REST API для управления библиотекой, разработанный на Django Rest Framework. 
Позволяет управлять книгами, авторами, пользователями, а также отслеживать выдачу и возврат книг. 
Аутентификация по JWT, документация по стандарту OpenAPI, контейнеризация через Docker.

## 📚 Стек технологий
- Python 3.14
- Django 6.1+
- Django Rest Framework
- PostgreSQL 16
- Simple JWT
- drf-spectacular (OpenAPI 3, Swagger UI)
- Docker, Docker Compose
- nginx
- gunicorn

## Требования

- Python 3.14+
- Git
- Poetry
- Docker и Docker Compose (для контейнеризации)
- PostgreSQL (локально или через Docker)

## Локальный запуск

1. Убедитесь, что у вас установлены требуемые программы
2. Клонируйте репозиторий:
    ```bash
    git clone https://github.com/GrandBalaxon/LibraryAPI.git
    cd LibraryAPI
    ```
3. Создайте и заполните `.env` (на основе `.env.example`). 
4. Установка зависимостей через `Poetry`:
    ```bash
    poetry install
    ```
5. Убедитесь, что PostgreSQL запущен локально, либо поднимите его в Docker, для этого выполните команду
    ```bash
    docker compose up db -d
    ```
6. Применение миграций
    ```bash
    python manage.py migrate
    ```
7. Создание суперпользователя (опционально)
    ```bash
    python manage.py createsuperuser
    ```
8. Запуск сервера разработки
    ```bash
    python manage.py runserver
    ```
   Проект будет доступен по адресу http://localhost:8000/.

## 🐳 Запуск через Docker Compose

1. Выполните 3 первые шага из предыдущей инструкции
2. Соберите образ
    ```bash
    docker compose up -d --build
    ```
   Проект будет доступен по адресу http://localhost/.

   После запуска контейнеров все миграции будут выполнены автоматически, дополнительных действий не требуется.

## 🧪 Тестовые данные (фикстура)

В проекте есть готовая фикстура с демонстрационными данными: пользователи, книги, авторы, издания, выдачи.  
Файл: `catalog/fixtures/test_data.json`

### Загрузка фикстуры

1. Убедитесь, что все миграции применены:
   ```bash
   python manage.py migrate
   ```
2. Загрузите данные:
   ```bash
   python manage.py loaddata catalog/fixtures/test_data.json
   ```

## 🔑 Основные эндпоинты

### 📖 Документация API

* `/api/docs/` - Swagger UI документация

* `/api/schema/` - OpenAPI схема

### Аутентификация

* `POST /api/user/register/` — регистрация нового читателя

* `POST /api/user/token/` — получение JWT (email, password)

* `POST /api/user/token/refresh/` — обновление access токена

### Пользователи

* `GET /api/user/` — список пользователей (только библиотекарь)

* `GET /api/user/{id}/` — конкретный пользователь (владелец или библиотекарь)

* `PATCH/PUT /api/user/{id}/` — редактирование профиля

* `DELETE /api/user/{id}/` — деактивация (только библиотекарь)

* `GET /api/user/me/` — свой профиль

* `POST /api/user/change-password/` — смена пароля

###  Каталог

* `GET/POST /api/catalog/authors/` — список/создание авторов

* `GET/PUT/PATCH/DELETE /api/catalog/authors/{id}/` — операции с автором

* `GET/POST /api/catalog/genres/` — жанры

* `GET/POST /api/catalog/publishers/` — издательства

* `GET/POST /api/catalog/books/` — произведения

* `GET/POST /api/catalog/editions/` — конкретные издания

* `POST /api/catalog/editions/{id}/add_copies/` — добавить копии

* `POST /api/catalog/editions/{id}/remove_copies/` — списать копии

### Выдача

* `GET/POST /api/lending/` — список/создание выдач

* `POST /api/lending/{id}/return/` — возврат книги

## 🔒 Роли и права доступа

* `Читатель` — может просматривать каталог, свои выдачи, редактировать свой профиль.

* `Библиотекарь` — полный доступ к каталогу, выдаче, списку пользователей.

## 🏗️ Структура проекта

```
LibraryAPI/
├── config/             # Основные настройки Django
│ ├── settings.py
│ ├── urls.py
│ └── wsgi.py
├── users/              # Пользователи: регистрация, профиль, JWT
│ ├── models.py         # CustomUser (роль, телефон, город)
│ ├── serializers.py
│ ├── views.py
│ ├── permissions.py    # IsLibrarian, IsLibrarianOrReadOnly, IsOwnerOrLibrarian
│ └── urls.py
├── catalog/            # Каталог: книги, авторы, издания, жанры, издатели
│ ├── models.py         # Book, Author, BookEdition, Genre, Publisher
│ ├── serializers.py
│ ├── views.py
│ ├── admin.py
│ └── urls.py
├── lending/            # Выдача книг
│ ├── models.py         # BookLoan
│ ├── serializers.py
│ ├── views.py
│ └── urls.py
├── api/                # Подключение роутеров (опционально)
├── .env.example        # Пример переменных окружения
├── Dockerfile
├── docker-compose.yml
├── pyproject.toml      # Зависимости и настройки линтеров
├── manage.py
└── README.md
```

## 📜 Лицензия

Этот проект распространяется под лицензией MIT.