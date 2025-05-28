"""
Точка входа WSGI для приложения.

Этот файл используется для запуска приложения с помощью командной строки
или WSGI-серверов (например, Gunicorn, uWSGI).
Он импортирует фабрику приложений `create_app` из пакета `src`
и создает экземпляр приложения.
"""

import os
from src.app import create_app

app = create_app()

if __name__ == "__main__":

    host = os.environ.get('FLASK_RUN_HOST', '127.0.0.1')
    try:
        port = int(os.environ.get('FLASK_RUN_PORT', '5000'))
    except ValueError:
        port = 5000
    app.run(host=host, port=port)
