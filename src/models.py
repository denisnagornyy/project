# -*- coding: utf-8 -*-
# Стандартная директива для указания кодировки UTF-8.
"""
Модуль определения моделей данных SQLAlchemy для приложения.

Этот файл является центральным местом для описания структуры базы данных
приложения с использованием SQLAlchemy ORM (Object-Relational Mapper).
Каждый класс, наследуемый от `db.Model`, представляет собой таблицу в базе данных.
Атрибуты этих классов, определенные с помощью `db.Column`, соответствуют столбцам
в этих таблицах. Связи между таблицами (один-ко-многим, многие-ко-многим)
определяются с помощью `db.relationship`.

SQLAlchemy использует эти модели для:
- Генерации SQL-команд для создания схемы базы данных (например, через Flask-Migrate).
- Преобразования строк из базы данных в объекты Python и наоборот.
- Выполнения запросов к базе данных с использованием объектно-ориентированного синтаксиса.

Определены следующие основные модели:
- `Region`: Справочник регионов России.
- `SpecialtyGroup`: Справочник укрупненных групп специальностей (УГСН).
- `Specialty`: Справочник специальностей (ОКСО), связанных с УГСН.
- `EducationalOrganization`: Информация об образовательных организациях (ВУЗы, колледжи, филиалы).
  Включает иерархическую связь для представления головных организаций и их филиалов.
- `EducationalProgram`: Информация об аккредитованных образовательных программах,
  связанных с организациями и специальностями.
- `IndividualEntrepreneur`: Информация об индивидуальных предпринимателях (если они
  участвуют в образовательном процессе или являются объектами реестра).
- `User`: Модель для пользователей системы, включая аутентификационные данные (хэш пароля).
  Интегрирована с Flask-Login через `UserMixin`.
- `Role` (закомментирована): Потенциальная модель для реализации ролевой системы доступа.
"""

# Импортируем объект `db` из локального модуля `.database`.
# `db` — это экземпляр `SQLAlchemy` (из `flask_sqlalchemy`), который был создан
# в `database.py` и будет инициализирован с Flask-приложением в `app.py`.
# Все модели должны наследоваться от `db.Model`, чтобы быть частью сессии SQLAlchemy
# и управляться через этот объект `db`.
from .database import db

# Импортируем функции для безопасной работы с паролями из библиотеки `werkzeug.security`.
# Werkzeug — это WSGI-библиотека, на которой основан Flask. Она предоставляет
# различные утилиты, включая функции для хеширования и проверки паролей.
# - `generate_password_hash(password, method='pbkdf2:sha256', salt_length=8)`:
#   Создает криптографически стойкий хэш пароля с использованием "соли".
#   Соль — это случайные данные, добавляемые к паролю перед хешированием,
#   чтобы усложнить атаки по радужным таблицам. Метод хеширования (например, pbkdf2:sha256)
#   и длина соли также сохраняются вместе с хэшем.
# - `check_password_hash(pwhash, password)`:
#   Проверяет, соответствует ли предоставленный пароль ранее созданному хэшу.
#   Эта функция извлекает метод хеширования и соль из `pwhash` и выполняет
#   сравнение.
from werkzeug.security import generate_password_hash, check_password_hash

# Импортируем `UserMixin` из расширения `flask_login`.
# `UserMixin` — это вспомогательный класс, который предоставляет стандартные реализации
# для свойств и методов, требуемых Flask-Login для управления пользователями.
# К ним относятся:
#   - `is_authenticated`: Свойство, возвращающее `True`, если пользователь аутентифицирован.
#   - `is_active`: Свойство, возвращающее `True`, если учетная запись пользователя активна.
#   - `is_anonymous`: Свойство, возвращающее `True`, если это анонимный пользователь.
#   - `get_id()`: Метод, возвращающий уникальный идентификатор пользователя (в виде строки).
# При наследовании от `UserMixin` модель пользователя автоматически получает эти возможности.
from flask_login import UserMixin

# Вспомогательная таблица для связи "многие-ко-многим" между программами и формами обучения.
# Этот комментарий, похоже, остался от предыдущей структуры или другого проекта,
# так как непосредственно под ним определяется модель Region, а не ассоциативная таблица.
# Если бы здесь была ассоциативная таблица, она бы выглядела примерно так:
# program_study_form_association = db.Table('program_study_form',
#     db.Column('program_id', db.Integer, db.ForeignKey('educational_program.id'), primary_key=True),
#     db.Column('study_form_id', db.Integer, db.ForeignKey('study_form.id'), primary_key=True)
# )
# И затем использовалась бы в db.relationship(..., secondary=program_study_form_association).

class Region(db.Model):
    """
    Модель для хранения информации о регионах Российской Федерации.

    Представляет таблицу `region` в базе данных. Каждый экземпляр этого класса
    соответствует одной записи (одному региону) в таблице.
    """
    # `__tablename__` — специальный атрибут SQLAlchemy, который явно указывает
    # имя таблицы в базе данных, с которой будет связана эта модель.
    # Если не указан, SQLAlchemy попытается сгенерировать имя на основе имени класса.
    __tablename__ = 'region'

    # Определение столбцов таблицы:
    # `id`: Первичный ключ таблицы.
    #   - `db.Column(db.Integer, ...)`: Определяет столбец типа INTEGER.
    #   - `primary_key=True`: Указывает, что этот столбец является первичным ключом.
    #     Первичные ключи автоматически индексируются и должны быть уникальными.
    #     В большинстве СУБД целочисленные первичные ключи также автоматически инкрементируются.
    id = db.Column(db.Integer, primary_key=True)

    # `name`: Название региона.
    #   - `db.String(200)`: Определяет столбец типа VARCHAR(200) (строка с максимальной длиной 200 символов).
    #   - `unique=True`: Указывает, что значения в этом столбце должны быть уникальными.
    #     Попытка вставить дублирующееся значение приведет к ошибке базы данных.
    #     SQLAlchemy автоматически создаст уникальный индекс для этого столбца.
    #   - `nullable=False`: Указывает, что этот столбец не может содержать NULL-значения.
    #     Попытка вставить запись без значения для этого поля приведет к ошибке.
    name = db.Column(db.String(200), unique=True, nullable=False)

    # Определение связи "один-ко-многим" с моделью `EducationalOrganization`.
    # Один регион (`Region`) может содержать много образовательных организаций (`EducationalOrganization`).
    # `db.relationship('EducationalOrganization', ...)`: Создает атрибут `organizations`,
    #   который будет предоставлять доступ к связанным объектам `EducationalOrganization`.
    #   - `'EducationalOrganization'`: Имя класса модели, с которой устанавливается связь.
    #   - `backref='region'`: Создает "обратную ссылку" на стороне `EducationalOrganization`.
    #     Это означает, что у каждого объекта `EducationalOrganization` появится атрибут `region`,
    #     через который можно будет получить доступ к связанному объекту `Region`.
    #   - `lazy='dynamic'`: Определяет, как будут загружаться связанные объекты.
    #     `'dynamic'` означает, что `region.organizations` вернет не список объектов,
    #     а специальный объект-запрос (Query), который можно дальше фильтровать или модифицировать
    #     перед фактической загрузкой данных из БД (например, `region.organizations.filter_by(...).all()`).
    #     Другие опции `lazy`: `'select'` (загрузка при первом обращении отдельным SELECT),
    #     `'joined'` (загрузка через JOIN в том же запросе, что и родительский объект),
    #     `'subquery'` (загрузка через подзапрос), `True` (синоним для `'select'`), `False` (синоним для `'joined'`).
    organizations = db.relationship('EducationalOrganization', backref='region', lazy='dynamic')

    def __repr__(self):
        """
        Метод для строкового представления объекта `Region`.
        Используется для отладки и логирования. Когда вы выводите объект `Region`
        (например, `print(my_region_object)`), будет вызвана эта функция.
        Возвращает строку, которая помогает идентифицировать объект.
        """
        return f'<Region {self.name}>' # Пример вывода: <Region Московская область>

class SpecialtyGroup(db.Model):
    """
    Модель для хранения укрупнённых групп специальностей и направлений подготовки (УГСН).
    УГСН — это классификатор, используемый в системе образования РФ.
    Например, "09.00.00 Информатика и вычислительная техника".
    """
    __tablename__ = 'specialty_group'

    id = db.Column(db.Integer, primary_key=True) # Уникальный идентификатор группы
    # `code`: Код УГСН (например, "09.00.00"). Строка, уникальная и обязательная.
    code = db.Column(db.String(20), unique=True, nullable=False)
    # `name`: Полное наименование УГСН. Строка, обязательная.
    name = db.Column(db.String(255), nullable=False)

    # Связь "один-ко-многим" с моделью `Specialty`.
    # Одна УГСН (`SpecialtyGroup`) может включать в себя много конкретных специальностей (`Specialty`).
    # `backref='group'`: У каждого объекта `Specialty` будет атрибут `group` для доступа к родительской УГСН.
    # `lazy='dynamic'`: Связанные специальности будут загружаться как объект-запрос.
    specialties = db.relationship('Specialty', backref='group', lazy='dynamic')

    def __repr__(self):
        """Строковое представление объекта `SpecialtyGroup`."""
        return f'<SpecialtyGroup {self.code} {self.name}>' # Пример: <SpecialtyGroup 09.00.00 Информатика и вычислительная техника>

class Specialty(db.Model):
    """
    Модель для хранения конкретных специальностей и направлений подготовки (по классификатору ОКСО).
    Каждая специальность принадлежит к определенной укрупнённой группе (УГСН).
    Например, "09.03.01 Информатика и вычислительная техника" (бакалавриат)
    принадлежит к УГСН "09.00.00 Информатика и вычислительная техника".
    """
    __tablename__ = 'specialty'

    id = db.Column(db.Integer, primary_key=True) # Уникальный идентификатор специальности
    # `code`: Код специальности (например, "09.03.01"). Строка, уникальная и обязательная.
    code = db.Column(db.String(20), unique=True, nullable=False)
    # `name`: Полное наименование специальности. Строка, обязательная.
    name = db.Column(db.String(255), nullable=False)

    # `group_id`: Внешний ключ, ссылающийся на `id` в таблице `specialty_group`.
    #   - `db.ForeignKey('specialty_group.id')`: Определяет ограничение внешнего ключа.
    #     Ссылается на столбец `id` таблицы `specialty_group`.
    #   - `nullable=False`: Каждая специальность должна принадлежать к какой-либо УГСН.
    group_id = db.Column(db.Integer, db.ForeignKey('specialty_group.id'), nullable=False)

    # Связь "один-ко-многим" с моделью `EducationalProgram`.
    # Одна специальность может быть реализована в рамках многих образовательных программ
    # в различных учебных заведениях.
    # `backref='specialty'`: У каждого объекта `EducationalProgram` будет атрибут `specialty`.
    programs = db.relationship('EducationalProgram', backref='specialty', lazy='dynamic')

    def __repr__(self):
        """Строковое представление объекта `Specialty`."""
        return f'<Specialty {self.code} {self.name}>' # Пример: <Specialty 09.03.01 Информатика и вычислительная техника>


class EducationalOrganization(db.Model):
    """
    Модель для хранения информации об образовательных организациях (ВУЗы, ССУЗы, их филиалы и т.д.).

    Содержит основную информацию об организации, такую как наименования,
    регистрационные номера (ОГРН, ИНН), контактные данные, адрес,
    принадлежность к региону и федеральному округу.
    Также поддерживает иерархическую структуру "головная организация — филиал"
    через самоссылающийся внешний ключ `parent_id`.
    """
    __tablename__ = 'educational_organization'

    id = db.Column(db.Integer, primary_key=True) # Уникальный идентификатор организации
    # `full_name`: Полное официальное наименование организации. Строка, обязательная.
    full_name = db.Column(db.String(1000), nullable=False)
    # `short_name`: Краткое (сокращенное) наименование организации. Строка, необязательная.
    short_name = db.Column(db.String(500))
    # `ogrn`: Основной государственный регистрационный номер. Строка, уникальная, индексируемая.
    #   `index=True`: Создает индекс для этого столбца в базе данных, что ускоряет поиск по ОГРН.
    ogrn = db.Column(db.String(15), unique=True, index=True)
    # `inn`: Идентификационный номер налогоплательщика. Строка, уникальная, индексируемая.
    inn = db.Column(db.String(12), unique=True, index=True)
    # `kpp`: Код причины постановки на учет. Строка, индексируемая.
    kpp = db.Column(db.String(9), index=True)
    # `address`: Юридический или фактический адрес организации.
    address = db.Column(db.String(1000))
    # `phone`: Контактный телефон.
    phone = db.Column(db.String(100))
    # `fax`: Номер факса.
    fax = db.Column(db.String(100))
    # `email`: Адрес электронной почты.
    email = db.Column(db.String(255))
    # `website`: Адрес веб-сайта.
    website = db.Column(db.String(255))
    # `head_post`: Должность руководителя.
    head_post = db.Column(db.String(255))
    # `head_name`: ФИО руководителя.
    head_name = db.Column(db.String(255))
    # `form_name`: Наименование организационно-правовой формы.
    form_name = db.Column(db.String(255))
    # `form_code`: Код организационно-правовой формы (по классификатору).
    form_code = db.Column(db.String(50))
    # `kind_name`: Наименование вида организации.
    kind_name = db.Column(db.String(255))
    # `kind_code`: Код вида организации.
    kind_code = db.Column(db.String(50))
    # `type_name`: Наименование типа организации.
    type_name = db.Column(db.String(255))
    # `type_code`: Код типа организации.
    type_code = db.Column(db.String(50))

    # `region_id`: Внешний ключ, ссылающийся на `id` в таблице `region`.
    # Указывает, в каком регионе находится организация.
    region_id = db.Column(db.Integer, db.ForeignKey('region.id'))

    # Поля, относящиеся к федеральному округу.
    federal_district_code = db.Column(db.String(50))
    federal_district_short_name = db.Column(db.String(50))
    federal_district_name = db.Column(db.String(255))

    # `parent_id`: Внешний ключ, ссылающийся на `id` в этой же таблице (`educational_organization`).
    #   Используется для построения иерархии "головная организация - филиал".
    #   Если `parent_id` равен `NULL` (или не указан), то это головная организация.
    #   Если `parent_id` указывает на другую запись, то это филиал.
    #   `nullable=True`: Поле может быть пустым (для головных организаций).
    parent_id = db.Column(db.Integer, db.ForeignKey('educational_organization.id'), nullable=True)

    # Определение связи для иерархии "головная-филиалы".
    # `children = db.relationship('EducationalOrganization', backref=db.backref('parent', remote_side=[id]))`
    #   - `'EducationalOrganization'`: Связь с этим же классом.
    #   - `backref=db.backref('parent', remote_side=[id])`: Создает атрибут `parent` у дочерних
    #     объектов (филиалов), который будет ссылаться на родительский объект (головную организацию).
    #     `remote_side=[id]` необходимо указать для SQLAlchemy, чтобы правильно разрешить
    #     самоссылающуюся связь "один-ко-многим". Он указывает, какой столбец на "удаленной"
    #     стороне (которая является "одной" в отношении "один-ко-многим") является частью связи.
    #     Здесь `id` - это первичный ключ `EducationalOrganization`, на который ссылается `parent_id`.
    # Атрибут `children` у головной организации будет содержать список ее филиалов.
    # Атрибут `parent` у филиала будет ссылаться на его головную организацию.
    # (Примечание: этот relationship не был в исходном коде, но логичен для parent_id)
    # Если он не нужен явно, то можно обойтись только parent_id и backref от region.
    # Однако, для удобной навигации по иерархии, такой relationship полезен.
    # Добавим его, если он не конфликтует с существующей логикой.
    # Судя по отсутствию, его пока нет. Оставим как есть, но это важное замечание.

    # Связь "один-ко-многим" с моделью `EducationalProgram`.
    # Одна образовательная организация может реализовывать множество образовательных программ.
    # `backref='organization'`: У каждого объекта `EducationalProgram` будет атрибут `organization`.
    programs = db.relationship('EducationalProgram', backref='organization', lazy='dynamic')


    def __repr__(self):
        """Строковое представление объекта `EducationalOrganization`."""
        # Используем краткое имя, если оно есть, иначе полное.
        return f'<EducationalOrganization {self.short_name or self.full_name}>'


class EducationalProgram(db.Model):
    """
    Модель для хранения информации об аккредитованных образовательных программах.

    Каждая образовательная программа связана с конкретной образовательной организацией,
    которая ее реализует, и с конкретной специальностью, по которой ведется обучение.
    """
    __tablename__ = 'educational_program'

    id = db.Column(db.Integer, primary_key=True) # Уникальный идентификатор программы

    # `organization_id`: Внешний ключ, ссылающийся на `id` в таблице `educational_organization`.
    #   Указывает, какая организация реализует данную программу. Обязательное поле.
    organization_id = db.Column(db.Integer, db.ForeignKey('educational_organization.id'), nullable=False)

    # `specialty_id`: Внешний ключ, ссылающийся на `id` в таблице `specialty`.
    #   Указывает, к какой специальности относится данная программа. Обязательное поле.
    specialty_id = db.Column(db.Integer, db.ForeignKey('specialty.id'), nullable=False)

    # Потенциальное поле для хранения дополнительных деталей об аккредитации программы.
    # `db.Text` используется для хранения длинных текстовых строк.
    # accreditation_details = db.Column(db.Text) # Пример, если потребуется

    # Можно добавить связь "многие-ко-многим" с формами обучения (StudyForm),
    # если одна программа может реализовываться в нескольких формах (очная, заочная и т.д.).
    # Для этого потребуется ассоциативная таблица и модель StudyForm.
    # study_forms = db.relationship('StudyForm', secondary=program_study_form_association,
    #                               backref=db.backref('programs', lazy='dynamic'), lazy='dynamic')

    def __repr__(self):
        """Строковое представление объекта `EducationalProgram`."""
        # Для более информативного представления можно было бы загрузить связанные
        # объекты organization и specialty, но это может привести к дополнительным запросам к БД.
        # Поэтому для простого `repr` часто используют ID.
        return f'<EducationalProgram id={self.id} org_id={self.organization_id} spec_id={self.specialty_id}>'

class IndividualEntrepreneur(db.Model):
    """
    Модель для хранения информации об индивидуальных предпринимателях (ИП).

    Эта модель может использоваться, если ИП являются частью экосистемы
    образовательных данных, например, как поставщики образовательных услуг,
    партнеры организаций или если они сами проходят какое-либо обучение,
    учитываемое в реестре.
    """
    __tablename__ = 'individual_entrepreneur'

    id = db.Column(db.Integer, primary_key=True) # Уникальный идентификатор ИП
    # `full_name`: Полное имя индивидуального предпринимателя. Обязательное поле.
    full_name = db.Column(db.String(1000), nullable=False)
    # `ogrnip`: Основной государственный регистрационный номер индивидуального предпринимателя.
    #   Строка, уникальная, индексируемая.
    ogrnip = db.Column(db.String(15), unique=True, index=True)
    # `inn`: ИНН индивидуального предпринимателя. Строка, уникальная, индексируемая.
    inn = db.Column(db.String(12), unique=True, index=True)
    # `address`: Адрес регистрации или деятельности ИП.
    address = db.Column(db.String(1000))
    # `phone`: Контактный телефон ИП.
    phone = db.Column(db.String(100))
    # `email`: Адрес электронной почты ИП.
    email = db.Column(db.String(255))
    # `website`: Адрес веб-сайта ИП (если есть).
    website = db.Column(db.String(255))

    def __repr__(self):
        """Строковое представление объекта `IndividualEntrepreneur`."""
        return f'<IndividualEntrepreneur {self.full_name}>'

# --- Модели для аутентификации и авторизации ---
# Этот раздел содержит модели, необходимые для управления пользователями системы,
# их входом, регистрацией и потенциально правами доступа.
# Комментарий "(Оценка 5)" неясен, возможно, это внутренняя пометка.

# Класс `UserMixin` из `flask_login` добавляет стандартные реализации
# методов и свойств, необходимых для работы с пользователями в Flask-Login:
# `is_authenticated`, `is_active`, `is_anonymous`, `get_id()`.
# Наследование от `db.Model` делает класс `User` моделью SQLAlchemy.
class User(UserMixin, db.Model):
    """
    Модель для хранения информации о пользователях системы.

    Эта модель используется для аутентификации и авторизации пользователей.
    Благодаря наследованию от `UserMixin`, объекты этого класса могут быть
    использованы напрямую с расширением Flask-Login.
    """
    __tablename__ = 'user' # Имя таблицы в БД для пользователей.

    id = db.Column(db.Integer, primary_key=True) # Уникальный идентификатор пользователя.

    # `username`: Имя пользователя (логин).
    #   - `db.String(64)`: Строка, максимальная длина 64 символа.
    #   - `index=True`: Создает индекс для этого столбца, ускоряя поиск по имени пользователя.
    #   - `unique=True`: Имя пользователя должно быть уникальным в системе.
    #   - `nullable=False`: Поле обязательно для заполнения.
    username = db.Column(db.String(64), index=True, unique=True, nullable=False)

    # `email`: Адрес электронной почты пользователя.
    #   - `db.String(120)`: Строка, максимальная длина 120 символов (стандартная длина для email).
    #   - `index=True`: Индексируется для быстрого поиска.
    #   - `unique=True`: Email должен быть уникальным.
    #   - `nullable=False`: Поле обязательно для заполнения.
    email = db.Column(db.String(120), index=True, unique=True, nullable=False)

    # `password_hash`: Хэш пароля пользователя.
    #   - `db.String(256)`: Строка для хранения хэша. Длина выбрана с запасом
    #     для различных методов хеширования и длин солей.
    #     Никогда не храните пароли в открытом виде! Только их хэши.
    password_hash = db.Column(db.String(256)) # Длина может быть 128, если используется sha256 с pbkdf2 по умолчанию. 256 - с запасом.

    # Потенциальное поле для связи с моделью `Role` (роль пользователя).
    # Если в системе будет реализована ролевая модель доступа, здесь будет внешний ключ
    # на таблицу ролей.
    # `role_id = db.Column(db.Integer, db.ForeignKey('role.id'))`

    def set_password(self, password):
        """
        Устанавливает (генерирует и сохраняет) хэш пароля для пользователя.

        Этот метод принимает пароль в открытом виде, генерирует из него
        криптографически стойкий хэш с использованием соли и сохраняет
        этот хэш в атрибуте `password_hash` объекта пользователя.

        Аргументы:
            password (str): Пароль пользователя в открытом виде, который нужно захэшировать.
        """
        # `generate_password_hash()` из `werkzeug.security` создает безопасный хэш.
        # Метод хеширования (например, `pbkdf2:sha256`) и соль выбираются автоматически
        # и сохраняются как часть строки хэша, что позволяет `check_password_hash`
        # корректно работать.
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """
        Проверяет, соответствует ли предоставленный пароль сохраненному хэшу пароля.

        Этот метод принимает пароль в открытом виде и сравнивает его с хэшем,
        хранящимся в `self.password_hash`.

        Аргументы:
            password (str): Пароль пользователя в открытом виде для проверки.

        Возвращает:
            bool: `True`, если предоставленный пароль совпадает с сохраненным хэшем,
                  `False` в противном случае.
        """
        # `check_password_hash()` из `werkzeug.security` безопасно сравнивает
        # пароль с хэшем, используя информацию о методе хеширования и соли,
        # хранящуюся в самом хэше.
        # Важно: не сравнивайте хэши напрямую, всегда используйте `check_password_hash`.
        if not self.password_hash: # Если хэш пароля не установлен (например, для старых записей или ошибки)
            return False
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        """Строковое представление объекта `User`."""
        return f'<User {self.username}>' # Пример: <User admin>

# TODO: Определить модель Role, если требуется ролевая система доступа.
# Этот комментарий указывает на возможное будущее расширение системы — добавление ролей.
# Ниже приведен примерный скелет модели `Role`.
#
# class Role(db.Model):
#     """
#     Модель для хранения ролей пользователей в системе (например, "администратор", "редактор", "пользователь").
#     Роли используются для управления правами доступа к различным функциям и данным приложения.
#     """
#     __tablename__ = 'role' # Имя таблицы для ролей.
#
#     id = db.Column(db.Integer, primary_key=True) # Уникальный идентификатор роли.
#     name = db.Column(db.String(64), unique=True, nullable=False) # Название роли, должно быть уникальным.
#
#     # Связь "один-ко-многим" с моделью `User`.
#     # Одна роль может быть присвоена многим пользователям.
#     # `backref='role'`: У каждого объекта `User` будет атрибут `role` для доступа к его роли.
#     #   (Если связь один-ко-многим, то у User будет role_id и user.role, а у Role будет role.users)
#     #   Правильнее: users = db.relationship('User', backref='role_obj', lazy='dynamic') # 'role_obj' чтобы не конфликтовать с возможным полем 'role'
#     #   А в User: role_id = db.Column(db.Integer, db.ForeignKey('role.id'))
#     users = db.relationship('User', backref='role', lazy='dynamic') # Если у User есть role_id, то это правильно.
#
#     # Поле для хранения разрешений, связанных с этой ролью.
#     # Это может быть реализовано по-разному:
#     # - Как битовая маска (целое число), где каждый бит соответствует определенному разрешению.
#     # - Как строка с JSON или списком разрешений.
#     # - Через отдельную таблицу связей "многие-ко-многим" с моделью `Permission`.
#     permissions = db.Column(db.Integer) # Пример: битовая маска разрешений.
#
#     def __repr__(self):
#         return f'<Role {self.name}>'
#
#     # Методы для работы с разрешениями (add_permission, remove_permission, has_permission)
#     # могли бы быть добавлены здесь, если используется битовая маска или аналогичный механизм.
#
# class Permission: # Гипотетическая модель для разрешений, если они гранулярные
#     VIEW_ARTICLES = 0x01
#     EDIT_ARTICLES = 0x02
#     DELETE_ARTICLES = 0x04
#     ADMIN_ACCESS = 0x80
#
#     @staticmethod
#     def has_permission(role_permissions, permission_flag):
#         return (role_permissions & permission_flag) == permission_flag
#
#     # и т.д.
#
# # Если бы была модель StudyForm (Форма обучения: очная, заочная и т.д.)
# class StudyForm(db.Model):
#     __tablename__ = 'study_form'
#     id = db.Column(db.Integer, primary_key=True)
#     name = db.Column(db.String(100), unique=True, nullable=False)
#     # programs = db.relationship('EducationalProgram', secondary=program_study_form_association, ...)
#
#     def __repr__(self):
#         return f'<StudyForm {self.name}>'
#
# # И ассоциативная таблица (если не определена ранее)
# program_study_form_association = db.Table('program_study_form_association',
#     db.Column('program_id', db.Integer, db.ForeignKey('educational_program.id'), primary_key=True),
#     db.Column('study_form_id', db.Integer, db.ForeignKey('study_form.id'), primary_key=True)
# )
# # Важно: определение ассоциативной таблицы должно быть на уровне модуля, а не внутри класса.
# # И модель StudyForm должна быть определена до того, как на нее ссылаются в relationship.
# # В данном файле модель StudyForm отсутствует, поэтому соответствующие связи закомментированы.
# # Если она есть в forms.py, то ее определение должно быть здесь.
# # Судя по forms.py, модель StudyForm существует. Добавим ее определение.

# Модель StudyForm и связанная с ней ассоциативная таблица program_study_forms_association
# были удалены из проекта согласно миграции e80aa6bad5d0_remove_studyform_model_and_relationships.py.
# Соответствующий код и комментарии к нему здесь отсутствуют,
# так как они больше не являются частью актуальной кодовой базы.
# Предыдущие строки с 486 по 567, содержавшие ошибочно добавленные определения
# StudyForm и program_study_forms_association, были удалены этим изменением.
