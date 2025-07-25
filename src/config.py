"""
Модуль конфигурации приложения Flask.

Этот файл отвечает за определение и загрузку всех конфигурационных параметров,
необходимых для работы приложения. Конфигурация может включать в себя:
- Секретные ключи (для подписи сессий, CSRF-токенов и т.д.).
- Строки подключения к базе данных.
- Пути к различным директориям (например, для временных файлов, логов).
- URL-адреса внешних сервисов и API.
- Флаги режимов работы (например, отладка, тестирование).

Основной подход заключается в использовании переменных окружения для хранения
чувствительных данных и настроек, специфичных для различных сред развертывания
(разработка, тестирование, продакшн). Файл `.env` используется для удобного
определения этих переменных в среде разработки.

Преимущества такого подхода:
1.  **Безопасность**: Секретные данные (пароли, API-ключи) не хранятся напрямую в коде
    и не попадают в систему контроля версий (если `.env` добавлен в `.gitignore`).
2.  **Гибкость**: Легко изменять конфигурацию для разных окружений без изменения кода.
3.  **Централизация**: Все настройки собраны в одном месте, что упрощает управление ими.
"""

import os

from dotenv import load_dotenv

basedir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

load_dotenv(os.path.join(basedir, '.env'))

class Config:
    """
    Класс для инкапсуляции всех настроек (конфигурационных переменных) приложения.

    Атрибуты этого класса представляют собой различные параметры конфигурации.
    Значения этих атрибутов либо жестко заданы, либо, что предпочтительнее
    для чувствительных данных или изменяемых параметров, загружаются из переменных окружения.
    Flask-приложение будет сконфигурировано с использованием объекта этого класса
    (или его дочерних классов для разных окружений, если это необходимо).
    """
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key'

    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'university_registry.db')

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    DATA_CACHE_PATH = os.path.join(basedir, 'data')

    ROSOBRNADZOR_DATA_URL = os.environ.get('ROSOBRNADZOR_DATA_URL') or 'URL_К_ДАННЫМ_РОСОБРНАДЗОРА'

config = Config()
