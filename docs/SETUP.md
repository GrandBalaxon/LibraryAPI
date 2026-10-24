# 🛠️ Руководство по установке и запуску

В этом документе описаны подробные шаги для развертывания проекта LibraryAPI.

## Требования

- Python 3.14+
- Git
- Poetry
- Docker и Docker Compose (опционально, для контейнеризации)
- PostgreSQL (локально или через Docker)

## 1. Подготовка

1. Клонируйте репозиторий:
   ```bash
   git clone https://github.com/GrandBalaxon/LibraryAPI.git
   cd LibraryAPI
   ```
2. Создайте и заполните `.env` (на основе `.env.example`). 

## 2. Локальный запуск (без Docker)

1. Установка зависимостей через `Poetry`:
    ```bash
    poetry install
    ```
2. Убедитесь, что PostgreSQL запущен локально, либо поднимите его в Docker, для этого выполните команду
    ```bash
    docker compose up db -d
    ```
3. Применение миграций
    ```bash
    python manage.py migrate
    ```
4. Создание суперпользователя (опционально)
    ```bash
    python manage.py createsuperuser
    ```
5. Запуск сервера разработки
    ```bash
    python manage.py runserver
    ```
   Проект будет доступен по адресу http://localhost:8000/.

## 3. 🐳 Запуск через Docker Compose (Production-ready)

1. Убедитесь, что `.env` файл настроен.
2. Соберите образ
    ```bash
    docker compose up -d --build
    ```
   Проект будет доступен по адресу http://localhost/.
   (Миграции внутри контейнера применяются автоматически при старте).

   После запуска контейнеров все миграции будут выполнены автоматически, дополнительных действий не требуется.

## 4. 🧪 Тестовые данные (фикстура)

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