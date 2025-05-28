"""
Модуль определения основных маршрутов (endpoints) веб-приложения с использованием Flask Blueprint.

Этот модуль отвечает за обработку HTTP-запросов к основным страницам и функциям приложения,
таким как:
- Главная страница (которая перенаправляет на реестр).
- Страница отображения реестра образовательных организаций с возможностями:
    - Фильтрации по региону, УГСН, специальности.
    - Сортировки по различным полям (наименование, ОГРН, ИНН, регион).
    - Пагинации (постраничного вывода) результатов.
- CRUD-операции (Create, Read, Update, Delete) для образовательных организаций.
- CRUD-операции для регионов (в разделе "администрирования").

Используется механизм Flask Blueprint (`main_bp`) для логической группировки этих маршрутов.
Это помогает структурировать приложение, особенно когда оно становится большим.
Маршруты защищены с помощью `@login_required` там, где это необходимо (например, для CRUD-операций).
Взаимодействие с базой данных осуществляется через модели SQLAlchemy (`EducationalOrganization`, `Region`, и т.д.)
и объект сессии `db.session`. Для обработки пользовательского ввода и его валидации используются
формы, определенные в `src.forms` (`FilterRegistryForm`, `OrganizationForm`, `RegionForm`).
"""

from flask import Blueprint, render_template, request, url_for, redirect, flash, abort

from sqlalchemy import asc, desc, distinct

from flask_login import login_required, current_user

from .models import EducationalOrganization, Region, Specialty, SpecialtyGroup, EducationalProgram

from .database import db

from .forms import FilterRegistryForm, OrganizationForm, RegionForm

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """
    Обработчик для главной (корневой) страницы сайта (URL: /).

    В текущей реализации эта функция не отображает собственную страницу,
    а немедленно перенаправляет пользователя на страницу реестра образовательных
    организаций (маршрут `show_registry`). Это сделано для того, чтобы
    пользователь сразу попадал к основному функционалу приложения.

    В будущем эта страница может быть доработана для отображения:
    - Приветственного сообщения.
    - Общей информации о проекте или системе.
    - Краткой статистики по данным реестра.
    - Новостей или важных объявлений.
    - Ссылок на основные разделы сайта.

    Возвращает:
        werkzeug.wrappers.Response: HTTP-ответ с перенаправлением (HTTP status code 302 Found)
                                    на URL, сгенерированный для маршрута `.show_registry`.
                                    Браузер пользователя автоматически перейдет по этому новому URL.
    """
    return redirect(url_for('.show_registry'))

@main_bp.route('/registry')
def show_registry():
    """
    Обработчик для отображения страницы реестра образовательных организаций.

    Эта функция является центральной для представления основного контента приложения.
    Она выполняет комплексную задачу по подготовке и отображению данных:
    1.  **Извлечение параметров из URL**: Получает значения для номера страницы (`page`),
        ключа сортировки (`sort_by`) и порядка сортировки (`sort_order`) из
        query string текущего HTTP-запроса. Если параметры отсутствуют,
        используются значения по умолчанию.
    2.  **Инициализация формы фильтрации**: Создает экземпляр формы `FilterRegistryForm`.
        В конструктор формы передаются `request.args` (параметры URL), что позволяет
        форме автоматически заполниться текущими значениями фильтров, если они были
        установлены пользователем ранее. Это обеспечивает "запоминание" состояния фильтров.
    3.  **Заполнение выпадающих списков формы**: Динамически загружает из базы данных
        списки регионов, укрупненных групп специальностей (УГСН) и конкретных
        специальностей. Эти данные используются для формирования вариантов выбора (`choices`)
        в соответствующих полях `SelectField` формы фильтрации. Это позволяет пользователю
        выбирать критерии фильтрации из актуальных данных.
    4.  **Построение основного запроса к БД**: Формирует базовый SQL-запрос (используя
        SQLAlchemy ORM) для выборки записей из таблицы `EducationalOrganization`.
        Используется `distinct()` для предотвращения дублирования организаций в результатах,
        которое может возникнуть из-за JOIN'ов при сложной фильтрации.
    5.  **Применение фильтров**: Динамически модифицирует основной запрос, добавляя
        к нему условия фильтрации (`.filter()`) на основе значений, выбранных
        пользователем в `filter_form`. Если фильтр не активен (например, выбрано "Все регионы"),
        соответствующее условие не добавляется. При необходимости выполняются JOIN'ы
        с другими таблицами (например, `EducationalProgram`, `Specialty`) для фильтрации
        по связанным данным.
    6.  **Применение сортировки**: Добавляет к запросу условие сортировки (`.order_by()`)
        на основе параметров `sort_by` и `sort_order`. При сортировке по полям
        из связанных таблиц (например, по названию региона) также выполняется JOIN.
    7.  **Пагинация**: Выполняет итоговый запрос с использованием `db.paginate()`.
        Эта функция извлекает из базы данных только ту "порцию" данных, которая
        соответствует запрошенной странице и заданному количеству записей на страницу.
        Это критически важно для производительности при работе с большими наборами данных.
    8.  **Рендеринг шаблона**: Передает полученный список организаций для текущей страницы,
        объект пагинации (для навигационных ссылок), текущие параметры сортировки
        и экземпляр формы фильтрации в HTML-шаблон `registry.html`. Шаблон Jinja2
        использует эти данные для динамической генерации HTML-кода страницы,
        отображая таблицу с организациями, элементы управления пагинацией,
        ссылки для сортировки и форму фильтров.

    Возвращает:
        str: Строка, содержащая HTML-код страницы реестра, сгенерированный
             на основе шаблона `registry.html` и переданных в него контекстных данных.
    """

    page = request.args.get('page', 1, type=int)
    
    sort_by = request.args.get('sort_by', 'name')

    sort_order = request.args.get('sort_order', 'asc')

    filter_form = FilterRegistryForm(request.args)

    regions = db.session.execute(db.select(Region).order_by(Region.name)).scalars().all()

    specialty_groups = db.session.execute(db.select(SpecialtyGroup).order_by(SpecialtyGroup.name)).scalars().all()

    specialties = db.session.execute(db.select(Specialty).order_by(Specialty.name)).scalars().all()

    filter_form.region.choices = [(r.id, r.name) for r in regions]
    filter_form.specialty_group.choices = [(sg.id, f"{sg.code} {sg.name}") for sg in specialty_groups]
    filter_form.specialty.choices = [(s.id, f"{s.code} {s.name}") for s in specialties]

    query = db.select(EducationalOrganization).distinct()

    if filter_form.region.data and filter_form.region.data != 0:
        query = query.filter(EducationalOrganization.region_id == filter_form.region.data)

    if filter_form.specialty_group.data and filter_form.specialty_group.data != 0:
  
        query = query.join(EducationalOrganization.programs)\
                     .join(EducationalProgram.specialty)\
                     .filter(Specialty.group_id == filter_form.specialty_group.data)

    if filter_form.specialty.data and filter_form.specialty.data != 0:
 
        if not (filter_form.specialty_group.data and filter_form.specialty_group.data != 0):
            query = query.join(EducationalOrganization.programs)

        query = query.filter(EducationalProgram.specialty_id == filter_form.specialty.data)

    sort_column = EducationalOrganization.full_name

    if sort_by == 'ogrn':
        sort_column = EducationalOrganization.ogrn
    elif sort_by == 'inn':
        sort_column = EducationalOrganization.inn
    elif sort_by == 'region':
        query = query.outerjoin(Region, EducationalOrganization.region_id == Region.id)
        sort_column = Region.name

    if sort_order == 'desc':
        query = query.order_by(desc(sort_column))
    else:
        query = query.order_by(asc(sort_column))
        sort_order = 'asc'
        
    pagination = db.paginate(query, page=page, per_page=20, error_out=False, max_per_page=100)

    organizations = pagination.items

    return render_template('registry.html',
                           organizations=organizations,  # Список объектов организаций для отображения на текущей странице.
                           pagination=pagination,      # Объект пагинации. Шаблон будет использовать его для генерации
                                                       # ссылок на другие страницы (например, `pagination.prev_num`,
                                                       # `pagination.next_num`, `pagination.iter_pages()`).
                           sort_by=sort_by,            # Текущее поле, по которому выполнена сортировка.
                                                       # Используется в шаблоне для подсветки активного столбца сортировки
                                                       # и для формирования URL-адресов для изменения поля сортировки.
                           sort_order=sort_order,      # Текущее направление сортировки ('asc' или 'desc').
                                                       # Используется в шаблоне для отображения текущего направления
                                                       # и для формирования URL-адресов для переключения направления.
                           filter_form=filter_form     # Экземпляр формы `FilterRegistryForm`.
                                                       # Используется в шаблоне для отображения полей фильтров
                                                       # и их текущих выбранных значений.
                           )

def _populate_organization_form_choices(form):
    """
    Вспомогательная (условно "приватная", по соглашению об именовании с начальным подчеркиванием) функция
    для динамического заполнения вариантов выбора (`choices`) в полях `SelectField`
    формы `OrganizationForm` (или любой другой формы с аналогичными полями `region` и `parent`).

    Эта функция инкапсулирует логику загрузки данных из базы для выпадающих списков,
    чтобы избежать дублирования кода в маршрутах добавления (`add_organization`)
    и редактирования (`edit_organization`) организаций.

    Действия функции:
    1.  **Загрузка регионов**: Выполняет запрос к базе данных для получения списка всех
        регионов (`Region`), отсортированных по названию.
    2.  **Загрузка головных организаций**: Выполняет запрос к базе данных для получения
        списка всех образовательных организаций (`EducationalOrganization`), которые
        сами не являются филиалами (т.е. у которых `parent_id` равен `None`).
        Эти организации могут выступать в качестве головных для других. Список
        сортируется по краткому наименованию.
    3.  **Формирование `choices` для поля "Регион"**: Создает список кортежей `(value, label)`
        для поля `form.region.choices`. В начало списка добавляется опция
        "--- Не выбрано ---" со значением `0`.
    4.  **Формирование `choices` для поля "Головная организация"**: Если в переданной
        форме `form` существует поле `parent` (проверяется через `hasattr`),
        аналогичным образом формируется список `choices` для него. В начало
        добавляется опция "--- Нет (Головная организация) ---" со значением `0`.

    Параметры:
        form (FlaskForm): Экземпляр формы (предположительно, `OrganizationForm` или
                          совместимой), содержащей поля `SelectField` с именами
                          `region` и, возможно, `parent`, атрибуты `choices` которых
                          необходимо заполнить.
    """
    regions = db.session.execute(db.select(Region).order_by(Region.name)).scalars().all()

    parents = db.session.execute(
        db.select(EducationalOrganization).filter(EducationalOrganization.parent_id.is_(None)).order_by(EducationalOrganization.short_name)
    ).scalars().all()

    form.region.choices = [(0, '--- Не выбрано ---')] + [(r.id, r.name) for r in regions]

    if hasattr(form, 'parent'):

        form.parent.choices = [(0, '--- Нет (Головная организация) ---')] + \
                              [(p.id, p.short_name or p.full_name) for p in parents]

@main_bp.route('/organization/add', methods=['GET', 'POST'])
@login_required
def add_organization():
    """
    Обработчик HTTP-запросов для страницы добавления новой образовательной организации.

    Эта функция управляет логикой отображения формы для добавления организации
    и обработкой данных, отправленных пользователем через эту форму.

    При GET-запросе:
    1.  Создается пустой экземпляр формы `OrganizationForm`.
    2.  Вызывается вспомогательная функция `_populate_organization_form_choices()`
        для динамического заполнения выпадающих списков (регионы, головные организации)
        в созданном экземпляре формы.
    3.  Отображается HTML-шаблон `organization_form.html`. В шаблон передаются:
        -   `title`: Заголовок для страницы ("Добавить организацию").
        -   `form`: Экземпляр формы (пустой, но с заполненными `choices`).

    При POST-запросе (когда пользователь заполнил и отправил форму):
    1.  Создается экземпляр формы `OrganizationForm`. Flask-WTF автоматически
        заполнит поля этой формы данными из `request.form` (данные, отправленные
        в теле POST-запроса).
    2.  Вызывается метод `form.validate_on_submit()`. Этот метод делает две вещи:
        a.  Проверяет, был ли запрос сделан методом POST.
        b.  Если да, то вызывает метод `form.validate()`, который запускает все
            валидаторы, определенные для полей формы (включая стандартные, такие как
            `DataRequired`, `Length`, и пользовательские, такие как `validate_ogrn`).
    3.  Если `form.validate_on_submit()` возвращает `True` (т.е. форма отправлена
        методом POST и все данные в ней валидны):
        a.  Создается новый объект модели `EducationalOrganization`.
        b.  Атрибуты этого объекта (соответствующие столбцам в таблице БД)
            заполняются данными из соответствующих полей формы (например,
            `new_org.full_name = form.full_name.data`). Значения строковых полей
            рекомендуется очищать от лишних пробелов с помощью `.strip()`.
            Для внешних ключей (`region_id`, `parent_id`) проверяется, было ли
            выбрано значение, отличное от "пустой" опции (которая имеет значение 0),
            и если да, то используется ID выбранной записи, иначе устанавливается `None`.
        c.  Новый объект организации добавляется в сессию SQLAlchemy с помощью
            `db.session.add(new_org)`. На этом этапе изменения еще не записаны в БД.
        d.  Выполняется попытка зафиксировать изменения в базе данных с помощью
            `db.session.commit()`. Это выполнит SQL INSERT-запрос.
        e.  Если сохранение в БД прошло успешно (`commit()` не вызвал исключений):
            -   Отображается flash-сообщение пользователю об успешном добавлении организации.
            -   Пользователь перенаправляется на страницу реестра организаций
                (URL генерируется с помощью `url_for('.show_registry')`).
        f.  Если при сохранении в БД произошла ошибка (например, `IntegrityError` из-за
            нарушения уникального ограничения, которое не было поймано валидатором формы,
            или любая другая ошибка СУБД):
            -   Транзакция откатывается с помощью `db.session.rollback()`, чтобы
                база данных осталась в согласованном состоянии.
            -   Отображается flash-сообщение пользователю об ошибке.
            -   (Обычно после этого происходит повторное отображение формы с ошибками,
                что происходит автоматически, так как `redirect` не выполняется).
    4.  Если `form.validate_on_submit()` возвращает `False` (т.е. запрос был GET,
        или это был POST-запрос, но форма не прошла валидацию):
        -   Отображается HTML-шаблон `organization_form.html`.
            -   Если это был GET-запрос, форма будет пустой (но с заполненными `choices`).
            -   Если это был POST-запрос с ошибками валидации, объект `form` будет
                содержать эти ошибки (в `form.errors`), а также данные, введенные
                пользователем. Шаблон может использовать эту информацию для отображения
                сообщений об ошибках рядом с соответствующими полями и для сохранения
                введенных пользователем корректных данных.

    Возвращает:
        str | werkzeug.wrappers.Response: Строка с HTML-кодом страницы (с формой для
                                          добавления организации) или HTTP-ответ
                                          с перенаправлением (после успешного добавления).
    """
  
    form = OrganizationForm()

    _populate_organization_form_choices(form)

    if form.validate_on_submit():

        new_org = EducationalOrganization(
            full_name=form.full_name.data.strip(),
            short_name=form.short_name.data.strip() if form.short_name.data else None,
            ogrn=form.ogrn.data.strip(),
            inn=form.inn.data.strip() if form.inn.data else None,
            address=form.address.data.strip() if form.address.data else None,

            region_id=form.region.data if form.region.data and form.region.data != 0 else None
        )

        if hasattr(form, 'parent'):
            new_org.parent_id = form.parent.data if form.parent.data and form.parent.data != 0 else None

        db.session.add(new_org)
        try:
            db.session.commit()

            flash('Организация успешно добавлена!', 'success')

            return redirect(url_for('.show_registry'))
        except Exception as e:
            db.session.rollback()

            flash(f'Ошибка при добавлении организации: {e}', 'error')

    return render_template('organization_form.html', title='Добавить организацию', form=form)

@main_bp.route('/organization/<int:org_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_organization(org_id):
    """
    Обработчик HTTP-запросов для страницы редактирования существующей образовательной организации.

    Эта функция позволяет пользователям изменять данные уже существующей в базе
    образовательной организации.

    Параметры:
        org_id (int): Идентификатор (первичный ключ) образовательной организации,
                      запись которой необходимо отредактировать. Это значение
                      извлекается из URL-адреса.

    При GET-запросе:
    1.  Из базы данных загружается объект `EducationalOrganization` с указанным `org_id`.
        Если организация с таким ID не найдена, автоматически возвращается ошибка 404 Not Found
        (благодаря использованию `db.get_or_404()`).
    2.  Создается экземпляр формы `OrganizationForm`. В конструктор формы передаются:
        -   `original_ogrn=organization.ogrn`: Текущее значение ОГРН организации.
            Это необходимо для пользовательского валидатора `validate_ogrn` в форме,
            чтобы он мог корректно проверить уникальность ОГРН (проверка не нужна,
            если ОГРН не изменился).
        -   `obj=organization`: Сам объект организации. WTForms использует этот объект
            для автоматического заполнения полей формы текущими значениями атрибутов
            организации (например, `form.full_name.data` будет равно `organization.full_name`).
    3.  Вызывается вспомогательная функция `_populate_organization_form_choices()`
        для заполнения выпадающих списков (регионы, головные организации) в форме.
    4.  Отображается HTML-шаблон `organization_form.html`. В шаблон передаются:
        -   `title`: Заголовок для страницы ("Редактировать организацию").
        -   `form`: Экземпляр формы, заполненный данными редактируемой организации.
        -   `organization`: Сам объект организации (может быть полезен в шаблоне
            для отображения дополнительной информации, не редактируемой через форму).

    При POST-запросе (когда пользователь отправил измененную форму):
    1.  Создается экземпляр формы `OrganizationForm`, автоматически заполненный
        данными из `request.form`. `original_ogrn` также передается.
    2.  Вызывается `form.validate_on_submit()`.
    3.  Если форма валидна:
        a.  Атрибуты существующего объекта `organization` (загруженного ранее из БД)
            обновляются данными из соответствующих полей формы.
            Рекомендуется использовать `.strip()` для строковых полей.
            Для внешних ключей (`region_id`, `parent_id`) значение 0 из формы
            интерпретируется как `None` (отсутствие связи).
        b.  Выполняется попытка зафиксировать изменения в базе данных (`db.session.commit()`).
            Это выполнит SQL UPDATE-запрос.
        c.  Если сохранение успешно:
            -   Отображается flash-сообщение об успехе.
            -   Пользователь перенаправляется на страницу реестра.
        d.  Если при сохранении произошла ошибка:
            -   Транзакция откатывается (`db.session.rollback()`).
            -   Отображается flash-сообщение об ошибке.
    4.  Если форма невалидна (при POST-запросе) или это GET-запрос:
        -   Отображается шаблон `organization_form.html` с формой (и ошибками, если были).

    Возвращает:
        str | werkzeug.wrappers.Response: HTML-страница с формой редактирования или
                                          HTTP-перенаправление после успешного обновления.
    """
    organization = db.get_or_404(EducationalOrganization, org_id)
    
    form = OrganizationForm(original_ogrn=organization.ogrn, obj=organization)

    _populate_organization_form_choices(form)

    if form.validate_on_submit():

        organization.full_name = form.full_name.data.strip()
        organization.short_name = form.short_name.data.strip() if form.short_name.data else None
        organization.ogrn = form.ogrn.data.strip()
        organization.inn = form.inn.data.strip() if form.inn.data else None
        organization.address = form.address.data.strip() if form.address.data else None
        organization.region_id = form.region.data if form.region.data and form.region.data != 0 else None
        if hasattr(form, 'parent'): # Обновляем parent_id только если поле parent есть в форме
            organization.parent_id = form.parent.data if form.parent.data and form.parent.data != 0 else None
        
        try:
            db.session.commit()
            flash('Данные организации успешно обновлены!', 'success')
            return redirect(url_for('.show_registry'))
        except Exception as e:
            db.session.rollback()
            flash(f'Ошибка при обновлении организации: {e}', 'error')

    return render_template('organization_form.html', title='Редактировать организацию', form=form, organization=organization)

    return render_template('organization_form.html', title='Редактировать организацию', form=form, organization=organization)

@main_bp.route('/organization/<int:org_id>/delete', methods=['POST'])
@login_required
def delete_organization(org_id):
    """
    Обработчик HTTP POST-запросов для удаления существующей образовательной организации.

    Эта функция выполняет следующие действия:
    1.  Загружает объект `EducationalOrganization` из базы данных по `org_id`,
        переданному в URL. Если организация не найдена, возвращается ошибка 404.
    2.  (Рекомендация) Выполняет проверку прав доступа текущего пользователя:
        имеет ли он разрешение на удаление организаций.
    3.  (Рекомендация) Выполняет проверку на наличие связанных данных (зависимостей),
        которые могут препятствовать удалению или требуют каскадного удаления
        (например, связанные образовательные программы). Если такие зависимости есть
        и не настроено автоматическое каскадное удаление на уровне БД или ORM,
        удаление может завершиться ошибкой или оставить "осиротевшие" записи.
    4.  Удаляет найденный объект организации из сессии SQLAlchemy (`db.session.delete()`).
    5.  Пытается зафиксировать изменения в базе данных (`db.session.commit()`), что
        приведет к выполнению SQL DELETE-запроса.
    6.  В случае успеха отображает flash-сообщение об успешном удалении.
    7.  В случае ошибки при удалении (например, из-за нарушения ограничений внешнего ключа,
        если не учтены зависимости) откатывает транзакцию и отображает flash-сообщение
        об ошибке. Также рекомендуется логировать такие ошибки.
    8.  В любом случае (успех или ошибка) перенаправляет пользователя обратно
        на страницу реестра организаций.

    Параметры:
        org_id (int): Идентификатор (первичный ключ) образовательной организации,
                      которую необходимо удалить.

    Возвращает:
        werkzeug.wrappers.Response: HTTP-ответ с перенаправлением на страницу реестра.
    """
    organization = db.get_or_404(EducationalOrganization, org_id)

    try:
        db.session.delete(organization)
        
        db.session.commit()

        flash(f'Организация "{organization.short_name or organization.full_name}" успешно удалена.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Ошибка при удалении организации: {e}', 'error')
    return redirect(url_for('.show_registry'))

@main_bp.route('/admin/regions')
@login_required
def admin_regions_list():
    """
    Обработчик для отображения списка регионов в административной панели.

    Загружает все регионы из базы данных, сортирует их по названию и
    передает в HTML-шаблон `admin/regions_list.html` для отображения.
    Этот шаблон должен содержать таблицу со списком регионов и, возможно,
    ссылки для добавления нового региона, редактирования и удаления существующих.

    Возвращает:
        str: HTML-страница со списком регионов.
    """

    regions = db.session.execute(db.select(Region).order_by(Region.name)).scalars().all()
    return render_template('admin/regions_list.html', regions=regions, title="Управление регионами")

@main_bp.route('/admin/regions/add', methods=['GET', 'POST'])
@login_required # НЕОБХОДИМА ПРОВЕРКА РОЛИ АДМИНИСТРАТОРА!
def admin_region_add():
    """
    Обработчик для добавления нового региона через административную панель.

    При GET-запросе отображает форму `RegionForm` для ввода названия нового региона.
    При POST-запросе (после отправки формы):
    - Валидирует данные формы.
    - Если форма валидна, создает новый объект `Region`, сохраняет его в базе данных.
    - Отображает flash-сообщение об успехе или ошибке.
    - Перенаправляет на страницу списка регионов.
    Если форма невалидна, повторно отображает форму с ошибками.

    Возвращает:
        str | werkzeug.wrappers.Response: HTML-страница с формой или перенаправление.
    """
    form = RegionForm()
    if form.validate_on_submit():
        region_name = form.name.data.strip()
        new_region = Region(name=region_name)
        db.session.add(new_region) # Добавляем новый регион в сессию.
        try:
            db.session.commit() # Сохраняем в БД.
            flash(f'Регион "{new_region.name}" успешно добавлен.', 'success')
            return redirect(url_for('.admin_regions_list')) # Перенаправляем на список регионов.
        except Exception as e: # Ловим общие исключения, но лучше конкретизировать (например, IntegrityError)
            db.session.rollback() # Откатываем транзакцию в случае ошибки.
            # Проверяем, не является ли ошибка ошибкой уникальности (если валидатор формы ее не поймал)
            # Это очень упрощенная проверка, в реальности может потребоваться более точный анализ типа исключения.
            if "UNIQUE constraint failed" in str(e).upper() or "duplicate key value violates unique constraint" in str(e).lower():
                 flash(f'Ошибка: Регион с названием "{region_name}" уже существует.', 'error')
            else:
                 flash(f'Ошибка при добавлении региона: {e}', 'error')
    return render_template('admin/region_form.html', form=form, title='Добавить регион')

@main_bp.route('/admin/regions/<int:region_id>/edit', methods=['GET', 'POST'])
@login_required # НЕОБХОДИМА ПРОВЕРКА РОЛИ АДМИНИСТРАТОРА!
def admin_region_edit(region_id):
    """
    Обработчик для редактирования существующего региона через административную панель.

    Параметры:
        region_id (int): ID региона для редактирования.

    При GET-запросе загружает регион, инициализирует форму `RegionForm` его данными
    и отображает шаблон с формой.
    При POST-запросе валидирует данные, обновляет регион в БД, обрабатывает ошибки
    и перенаправляет на список регионов.

    Возвращает:
        str | werkzeug.wrappers.Response: HTML-страница с формой или перенаправление.
    """
    # TODO: Заменить на проверку роли администратора.
    region = db.get_or_404(Region, region_id) # Загружаем регион или получаем 404.
    form = RegionForm(original_name=region.name, obj=region)
    if form.validate_on_submit():
        region.name = form.name.data.strip() # Обновляем название региона.
        try:
            db.session.commit() # Сохраняем изменения.
            flash(f'Регион "{region.name}" успешно обновлен.', 'success')
            return redirect(url_for('.admin_regions_list'))
        except Exception as e:
            db.session.rollback()
            if "UNIQUE constraint failed" in str(e).upper() or "duplicate key value violates unique constraint" in str(e).lower():
                 flash(f'Ошибка: Регион с названием "{region.name}" уже существует (возможно, вы пытаетесь переименовать в уже существующее название).', 'error')
            else:
                 flash(f'Ошибка при обновлении региона: {e}', 'error')
    # Отображаем шаблон с формой (при GET или если POST невалиден).
    return render_template('admin/region_form.html', form=form, title='Редактировать регион', region=region)

@main_bp.route('/admin/regions/<int:region_id>/delete', methods=['POST'])
@login_required # НЕОБХОДИМА ПРОВЕРКА РОЛИ АДМИНИСТРАТОРА!
def admin_region_delete(region_id):
    """
    Обработчик для удаления региона через административную панель.

    Параметры:
        region_id (int): ID региона для удаления.

    Загружает регион, проверяет зависимости (наличие организаций в этом регионе),
    удаляет регион из БД, обрабатывает ошибки и перенаправляет на список регионов.

    Возвращает:
        werkzeug.wrappers.Response: Перенаправление на список регионов.
    """
    region = db.get_or_404(Region, region_id)
    try:
        if region.organizations.count() > 0:
            flash(f'Невозможно удалить регион "{region.name}", так как он используется образовательными организациями. '
                  'Сначала измените регион у этих организаций или удалите их.', 'danger')
            return redirect(url_for('.admin_regions_list'))

        db.session.delete(region) # Удаляем регион из сессии.
        db.session.commit() # Фиксируем удаление в БД.
        flash(f'Регион "{region.name}" успешно удален.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Ошибка при удалении региона: {e}', 'error')
        # Логирование ошибки.
    return redirect(url_for('.admin_regions_list')) # Перенаправляем на список регионов.
