"""
Модуль определения форм WTForms для веб-приложения.

Этот модуль является центральным местом для определения всех форм,
используемых в приложении для сбора и валидации пользовательского ввода.
Формы создаются с использованием библиотеки Flask-WTF, которая является
интеграцией WTForms с Flask и предоставляет удобства, такие как защита от CSRF,
интеграция с шаблонизатором Jinja2 и упрощенная обработка данных формы.

Здесь определены следующие типы форм:
- Формы для аутентификации пользователей (`LoginForm`, `RegistrationForm`).
- Формы для фильтрации данных в реестре (`FilterRegistryForm`).
- Формы для операций CRUD (Create, Read, Update, Delete) над сущностями
  (например, `OrganizationForm`, `StudyFormForm`, `RegionForm`).

Каждая форма представляет собой класс, наследуемый от `FlaskForm`.
Поля формы определяются как атрибуты класса, используя различные типы полей
из WTForms (например, `StringField`, `PasswordField`, `SelectField`).
Валидаторы (например, `DataRequired`, `Email`, `Length`, `EqualTo`)
применяются к полям для проверки корректности введенных данных.
Также могут быть определены пользовательские методы валидации для более сложной логики.
"""
from flask_wtf import FlaskForm

from wtforms import StringField, PasswordField, BooleanField, SubmitField, SelectField, TextAreaField

from wtforms.validators import DataRequired, Email, EqualTo, ValidationError, Optional, Length

from .models import User, Region, EducationalOrganization

from .database import db

class FilterRegistryForm(FlaskForm):
    """
    Форма для фильтрации записей в реестре образовательных организаций.

    Эта форма позволяет пользователю задать критерии для отбора организаций,
    отображаемых на странице реестра. Включает поля для выбора региона,
    укрупненной группы специальностей (УГСН) и конкретной специальности.
    Все поля являются необязательными, что позволяет пользователю применять
    фильтры гибко.
    """

    region = SelectField('Регион', coerce=int, validators=[Optional()], default=0)

    specialty_group = SelectField('Укрупненная группа', coerce=int, validators=[Optional()], default=0)

    specialty = SelectField('Специальность', coerce=int, validators=[Optional()], default=0)

    submit = SubmitField('Применить фильтры')

    def __init__(self, *args, **kwargs):
        """
        Конструктор формы `FilterRegistryForm`.

        Вызывает конструктор родительского класса `FlaskForm` и затем модифицирует
        списки `choices` для полей `SelectField`, добавляя в начало каждого списка
        опцию "Все ..." (например, "Все регионы"). Это позволяет пользователю
        легко сбросить соответствующий фильтр.

        Параметры:
            *args: Позиционные аргументы, передаваемые в конструктор родительского класса.
            **kwargs: Именованные аргументы, передаваемые в конструктор родительского класса.
                      Сюда могут входить, например, `request.form` для заполнения формы данными.
        """

        super(FilterRegistryForm, self).__init__(*args, **kwargs)

        if self.region.choices and self.region.choices[0][0] != 0:

            self.region.choices.insert(0, (0, 'Все регионы'))

        if self.specialty_group.choices and self.specialty_group.choices[0][0] != 0:
            self.specialty_group.choices.insert(0, (0, 'Все группы'))

        if self.specialty.choices and self.specialty.choices[0][0] != 0:
            self.specialty.choices.insert(0, (0, 'Все специальности'))

class LoginForm(FlaskForm):
    """
    Форма для входа (аутентификации) пользователя в систему.

    Содержит поля для ввода имени пользователя (или email) и пароля,
    а также опциональный чекбокс "Запомнить меня".
    """
    
    username_or_email = StringField('Имя пользователя или Email',
                                    validators=[DataRequired(message="Это поле обязательно.")])

    password = PasswordField('Пароль',
                             validators=[DataRequired(message="Это поле обязательно.")])

    remember_me = BooleanField('Запомнить меня')

    submit = SubmitField('Войти')


class RegistrationForm(FlaskForm):
    """
    Форма для регистрации нового пользователя в системе.

    Содержит поля для ввода имени пользователя, email, пароля и подтверждения пароля.
    Включает валидаторы для проверки обязательности полей, формата email,
    длины имени пользователя и пароля, а также совпадения паролей.
    Также содержит пользовательские валидаторы для проверки уникальности
    имени пользователя и email в базе данных.
    """
 
    username = StringField('Имя пользователя',
                           validators=[DataRequired(message="Это поле обязательно."),
                                       Length(min=3, max=64, message="Имя пользователя должно быть от 3 до 64 символов.")])

    email = StringField('Email',
                        validators=[DataRequired(message="Это поле обязательно."),
                                    Email(message="Некорректный формат Email.")])

    password = PasswordField('Пароль',
                             validators=[DataRequired(message="Это поле обязательно."),
                                         Length(min=6, message="Пароль должен быть не менее 6 символов.")])

    password2 = PasswordField(
        'Повторите пароль', validators=[DataRequired(message="Это поле обязательно."),
                                     EqualTo('password', message='Пароли должны совпадать.')])

    submit = SubmitField('Зарегистрироваться')

    def validate_username(self, username_field):
        """
        Пользовательский валидатор для поля `username`.
        Проверяет, не занято ли введенное имя пользователя другим пользователем в базе данных.

        Параметры:
            username_field (wtforms.fields.StringField): Объект поля `username` из формы.
                                                        Его значение доступно через `username_field.data`.
        """
        user = db.session.scalar(db.select(User).filter_by(username=username_field.data))

        if user is not None:
            raise ValidationError('Это имя пользователя уже занято. Пожалуйста, выберите другое.')

    def validate_email(self, email_field):
        """
        Пользовательский валидатор для поля `email`.
        Проверяет, не зарегистрирован ли уже пользователь с таким email-адресом.

        Параметры:
            email_field (wtforms.fields.StringField): Объект поля `email` из формы.
                                                     Его значение доступно через `email_field.data`.
        """
        user = db.session.scalar(db.select(User).filter_by(email=email_field.data))
        if user is not None:
            raise ValidationError('Этот email уже зарегистрирован. Пожалуйста, используйте другой.')

class OrganizationForm(FlaskForm):
    """
    Форма для добавления или редактирования информации об образовательной организации.

    Эта форма используется для сбора данных, необходимых для создания новой записи
    об образовательной организации или для обновления существующей.
    Включает поля для наименования, ОГРН, ИНН, адреса и региона.
    """

    full_name = StringField('Полное наименование', validators=[DataRequired(message="Полное наименование обязательно для заполнения.")])

    short_name = StringField('Краткое наименование', validators=[Optional()])

    ogrn = StringField('ОГРН', validators=[DataRequired(message="ОГРН обязателен."),
                                          Length(min=13, max=15, message="ОГРН должен содержать 13 или 15 цифр.")])

    inn = StringField('ИНН', validators=[Optional(),
                                        Length(min=10, max=12, message="ИНН должен содержать 10 или 12 цифр.")])

    address = TextAreaField('Адрес', validators=[Optional()])

    region = SelectField('Регион', coerce=int, validators=[Optional()])

    submit = SubmitField('Сохранить')

    def __init__(self, original_ogrn=None, *args, **kwargs):
        """
        Конструктор формы `OrganizationForm`.

        Инициализирует форму и сохраняет оригинальное значение ОГРН (`original_ogrn`),
        если оно передано. Это необходимо для корректной работы валидатора уникальности ОГРН
        при редактировании существующей организации (чтобы не возникало ошибки, если ОГРН не менялся).

        Параметры:
            original_ogrn (str, optional): Оригинальное значение ОГРН редактируемой организации.
                                           Передается, если форма используется для редактирования.
                                           По умолчанию `None` (для создания новой организации).
            *args, **kwargs: Стандартные аргументы для конструктора `FlaskForm`.
        """
        super(OrganizationForm, self).__init__(*args, **kwargs)
      
        self.original_ogrn = original_ogrn

    def validate_ogrn(self, ogrn_field):
        """
        Пользовательский валидатор для поля `ogrn`.
        Проверяет уникальность ОГРН в базе данных.
        При редактировании организации, если ОГРН не изменился, проверка уникальности пропускается.

        Параметры:
            ogrn_field (wtforms.fields.StringField): Объект поля `ogrn`.
        """
        if self.original_ogrn and self.original_ogrn == ogrn_field.data:
            return

        organization = db.session.scalar(db.select(EducationalOrganization).filter_by(ogrn=ogrn_field.data))
        if organization:
            raise ValidationError('Организация с таким ОГРН уже существует в базе данных.')

    def validate_inn(self, inn_field):
        """
        Пользовательский валидатор для поля `inn`.
        Проверяет уникальность ИНН в базе данных, если ИНН указан.
        Аналогично ОГРН, при редактировании можно было бы добавить проверку
        на изменение ИНН, если бы передавался `original_inn`.

        Параметры:
            inn_field (wtforms.fields.StringField): Объект поля `inn`.
        """

        if not inn_field.data:
            return

        organization = db.session.scalar(db.select(EducationalOrganization).filter_by(inn=inn_field.data))
        if organization:
            raise ValidationError('Организация с таким ИНН уже существует в базе данных.')

class StudyFormForm(FlaskForm):
    """
    Форма для добавления или редактирования формы обучения (например, "Очная", "Заочная").

    Содержит поле для названия формы обучения и кнопку сохранения.
    Включает валидатор для проверки уникальности названия.
    """

    name = StringField('Название формы обучения', validators=[DataRequired(message="Название формы обучения обязательно."),
                                                            Length(max=100, message="Название не должно превышать 100 символов.")])
    submit = SubmitField('Сохранить')

    def __init__(self, original_name=None, *args, **kwargs):
        """
        Конструктор формы `StudyFormForm`.

        Сохраняет оригинальное название формы обучения для проверки уникальности при редактировании.

        Параметры:
            original_name (str, optional): Оригинальное название редактируемой формы обучения.
            *args, **kwargs: Стандартные аргументы для конструктора `FlaskForm`.
        """
        super(StudyFormForm, self).__init__(*args, **kwargs)
        self.original_name = original_name

    def validate_name(self, name_field):
        """
        Пользовательский валидатор для поля `name` (название формы обучения).
        Проверяет уникальность названия формы обучения в базе данных, игнорируя регистр символов.
        При редактировании, если название не изменилось (с учетом регистра), проверка пропускается.

        Параметры:
            name_field (wtforms.fields.StringField): Объект поля `name`.
        """
        from .models import StudyForm

        form_entry = db.session.scalar(
            db.select(StudyForm).filter(db.func.lower(StudyForm.name) == name_field.data.lower())
        )
      
        if form_entry and (not self.original_name or name_field.data.lower() != self.original_name.lower()):
            raise ValidationError('Форма обучения с таким названием уже существует.')

class RegionForm(FlaskForm):
    """
    Форма для добавления или редактирования региона.

    Содержит поле для названия региона и кнопку сохранения.
    Включает валидатор для проверки уникальности названия региона.
    """
    name = StringField('Название региона', validators=[DataRequired(message="Название региона обязательно."),
                                                     Length(max=200, message="Название не должно превышать 200 символов.")])
    submit = SubmitField('Сохранить')

    def __init__(self, original_name=None, *args, **kwargs):
        """
        Конструктор формы `RegionForm`.

        Сохраняет оригинальное название региона для проверки уникальности при редактировании.

        Параметры:
            original_name (str, optional): Оригинальное название редактируемого региона.
            *args, **kwargs: Стандартные аргументы для конструктора `FlaskForm`.
        """
        super(RegionForm, self).__init__(*args, **kwargs)
        self.original_name = original_name

    def validate_name(self, name_field):
        """
        Пользовательский валидатор для поля `name` (название региона).
        Проверяет уникальность названия региона в базе данных, игнорируя регистр.
        При редактировании, если название не изменилось (с учетом регистра), проверка пропускается.

        Параметры:
            name_field (wtforms.fields.StringField): Объект поля `name`.
        """
        region_entry = db.session.scalar(
            db.select(Region).filter(db.func.lower(Region.name) == name_field.data.lower())
        )
        if region_entry and (not self.original_name or name_field.data.lower() != self.original_name.lower()):
            raise ValidationError('Регион с таким названием уже существует.')
