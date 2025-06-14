"""
Основной модуль Flask-приложения. Точка сборки и инициализации всех компонентов.

Этот файл является сердцем всего веб-приложения. Его главная задача — создать
и сконфигурировать экземпляр Flask-приложения, который затем будет использоваться
веб-сервером (например, Gunicorn или встроенным сервером Flask для разработки)
для обработки входящих HTTP-запросов.

Здесь происходит последовательная инициализация и подключение всех ключевых частей приложения:
- Импорт необходимых библиотек и модулей:
    - `Flask`: основной класс для создания веб-приложения.
    - `Config`: класс, содержащий конфигурационные параметры (секретный ключ, настройки БД и т.д.).
    - `database`: модуль, отвечающий за работу с базой данных (SQLAlchemy).
    - `Migrate`: расширение Flask-Migrate для управления миграциями схемы базы данных.
    - `models`: модуль, описывающий структуру данных приложения (таблицы БД).
    - `commands`: модуль, содержащий пользовательские команды для интерфейса командной строки (CLI).
    - `LoginManager`: расширение Flask-Login для управления аутентификацией пользователей.
    - `main_bp`, `auth_bp`: "чертежи" (Blueprints) для разделения маршрутов на логические группы.
- Создание объекта приложения Flask (`app = Flask(__name__)`).
- Загрузка конфигурации из объекта `Config` (например, `app.config.from_object(Config)`).
- Инициализация расширения SQLAlchemy для работы с базой данных (`init_db(app)`).
- Инициализация Flask-Migrate для управления версиями схемы базы данных (`Migrate(app, db)`).
- Инициализация Flask-Login для управления сессиями пользователей (`login_manager.init_app(app)`).
- Регистрация пользовательских команд CLI, доступных через команду `flask` (например, `app.cli.add_command(data_cli)`).
- Регистрация "чертежей" (Blueprints), которые определяют маршруты и связанные с ними функции-обработчики.
- Определение контекстных процессоров для добавления переменных в глобальный контекст шаблонов Jinja2.
- Настройка точки входа для запуска сервера разработки (хотя в данном файле это неявно, запуск происходит через `wsgi.py` или `flask run`).
"""
from flask import Flask

from flask_migrate import Migrate

from .config import Config

from .database import db, init_db

from . import models

from .commands import data_cli

from .routes import main_bp
from .auth_routes import auth_bp

from flask_login import LoginManager

login_manager = LoginManager()

login_manager.login_view = 'auth.login'

login_manager.login_message = 'Пожалуйста, войдите в систему для доступа к этой странице.'

login_manager.login_message_category = 'info'

@login_manager.user_loader
def load_user(user_id):
    """
    Функция для загрузки пользователя по его идентификатору (user_id).
    Flask-Login вызывает эту функцию при каждом запросе, если пользователь ранее вошел в систему.
    Она получает `user_id` (обычно первичный ключ пользователя в таблице `users`) из сессионного cookie
    и должна вернуть соответствующий объект пользователя или `None`, если пользователь не найден.

    Аргументы:
        user_id (str): Идентификатор пользователя, извлеченный из сессии. Flask-Login передает его как строку.

    Возвращает:
        User | None: Объект пользователя, если он найден в базе данных, иначе None.
    """
    from .models import User

    return db.session.get(User, int(user_id))

def create_app(config_class=Config):
    """
    Эта функция-фабрика создает, конфигурирует и возвращает экземпляр приложения Flask.
    Использование фабрики имеет несколько преимуществ:
    1.  Позволяет создавать несколько экземпляров приложения с разными конфигурациями
        (например, одно для разработки, другое для тестирования, третье для продакшена).
    2.  Помогает избежать циклических импортов, так как экземпляр приложения создается
        внутри функции, и к нему можно обращаться только после его создания.
    3.  Упрощает тестирование, так как можно легко создать "чистый" экземпляр приложения для каждого теста.

    Аргументы:
        config_class (class, optional): Класс, содержащий конфигурационные параметры.
                                         По умолчанию используется `Config` из модуля `src.config`.

    Возвращает:
        Flask: Сконфигурированный и готовый к работе экземпляр приложения Flask.
    """
    app = Flask(__name__)

    app.config.from_object(config_class)

    init_db(app)
   
    migrate = Migrate(app, db) ё
    login_manager.init_app(app)

    app.cli.add_command(data_cli)

    app.register_blueprint(main_bp)
   
    app.register_blueprint(auth_bp)

    @app.context_processor
    def inject_current_year():
        """
        Эта функция-контекстный процессор добавляет переменную `current_year`
        в контекст каждого шаблона. Это позволяет легко отображать текущий год,
        например, в футере сайта, без необходимости передавать его вручную
        в каждой функции-обработчике маршрута.

        Возвращает:
            dict: Словарь, ключи которого становятся переменными в шаблонах.
        """
        from datetime import datetime

        return dict(current_year=datetime.utcnow().year)

    return app
