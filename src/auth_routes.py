"""
Модуль определения маршрутов для аутентификации и авторизации пользователей (Blueprint 'auth').

Этот модуль инкапсулирует всю логику, связанную с управлением учетными записями пользователей:
- Регистрация новых пользователей.
- Вход существующих пользователей в систему (аутентификация).
- Выход пользователей из системы.
- Потенциально (в будущем) — восстановление пароля, смена пароля и другие связанные функции.

Используется механизм Flask Blueprints для модульной организации маршрутов.
Все маршруты, определенные в этом файле, будут иметь префикс '/auth' (например, '/auth/login', '/auth/register').
"""

from flask import Blueprint, render_template, redirect, url_for, flash, request

from flask_login import login_user, logout_user, current_user, login_required

from urllib.parse import urlparse

from .forms import LoginForm, RegistrationForm

from .models import User

from .database import db

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """
    Функция-обработчик для страницы входа пользователя (/auth/login).

    Логика работы:
    1. Если пользователь уже аутентифицирован, он перенаправляется на главную страницу реестра.
    2. Создается экземпляр формы `LoginForm`.
    3. Если запрос является POST-запросом и форма успешно прошла валидацию (`form.validate_on_submit()`):
        a. Извлекаются данные из полей формы (имя пользователя/email и пароль).
        b. Производится поиск пользователя в базе данных по имени пользователя или email.
        c. Если пользователь найден и введенный пароль корректен:
            i. Пользователь регистрируется в системе с помощью `login_user()`.
            ii. Отображается приветственное flash-сообщение.
            iii. Пользователь перенаправляется на страницу, которую он пытался посетить до входа (`next_page`),
               или на главную страницу реестра, если `next_page` не указана или небезопасна.
        d. Если пользователь не найден или пароль неверен:
            i. Отображается flash-сообщение об ошибке.
            ii. Пользователь перенаправляется обратно на страницу входа.
    4. Если запрос является GET-запросом или форма не прошла валидацию:
        a. Отображается HTML-шаблон страницы входа (`auth/login.html`) с формой.
    """
    if current_user.is_authenticated:
        return redirect(url_for('main.show_registry'))
        
    form = LoginForm()

    if form.validate_on_submit():
        login_identifier = form.username_or_email.data

        user = db.session.scalar(
            db.select(User).filter(
                (User.username == login_identifier) | (User.email == login_identifier)
            )
        )

        if user is None or not user.check_password(form.password.data):
            flash('Неверное имя пользователя/email или пароль.', 'error')
            return redirect(url_for('.login'))

        login_user(user, remember=form.remember_me.data)
        flash(f'Добро пожаловать, {user.username}!', 'success')
        next_page = request.args.get('next')

        if not next_page or urlparse(next_page).netloc != '':
            next_page = url_for('main.show_registry')
        return redirect(next_page)
    return render_template('auth/login.html', title='Вход', form=form)
@auth_bp.route('/logout')
@login_required
def logout():
    """
    Функция-обработчик для выхода пользователя из системы (/auth/logout).

    Логика работы:
    1. Вызывается функция `logout_user()` из Flask-Login, которая удаляет данные пользователя из сессии.
    2. Отображается flash-сообщение об успешном выходе.
    3. Пользователь перенаправляется на главную страницу реестра.
    """

    logout_user()
    flash('Вы успешно вышли из системы.', 'info')
    return redirect(url_for('main.show_registry'))

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """
    Функция-обработчик для страницы регистрации нового пользователя (/auth/register).

    Логика работы:
    1. Если пользователь уже аутентифицирован, он перенаправляется на главную страницу реестра.
    2. Создается экземпляр формы `RegistrationForm`.
    3. Если запрос является POST-запросом и форма успешно прошла валидацию (`form.validate_on_submit()`):
        a. Извлекаются данные из полей формы (имя пользователя, email, пароль).
        b. Создается новый объект `User`.
        c. Устанавливается пароль для нового пользователя (пароль хешируется перед сохранением).
        d. Новый пользователь добавляется в сессию базы данных и сохраняется (`db.session.add()`, `db.session.commit()`).
        e. Отображается flash-сообщение об успешной регистрации.
        f. Пользователь перенаправляется на страницу входа.
    4. Если запрос является GET-запросом или форма не прошла валидацию:
        a. Отображается HTML-шаблон страницы регистрации (`auth/register.html`) с формой.
    """
    if current_user.is_authenticated:
        return redirect(url_for('main.show_registry'))

    form = RegistrationForm()

    if form.validate_on_submit():

        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Поздравляем, вы успешно зарегистрированы! Теперь вы можете войти.', 'success')
        return redirect(url_for('.login'))

    return render_template('auth/register.html', title='Регистрация', form=form)
