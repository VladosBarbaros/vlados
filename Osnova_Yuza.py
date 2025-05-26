import logging
import requests
import phonenumbers
from phonenumbers import geocoder, carrier
import time
import io
import re
import json
from html import escape

from telegram import (
    Update,
    KeyboardButton,
    ReplyKeyboardMarkup
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    CallbackContext,
    filters,
)
from telegram.error import Forbidden

# =========================== НАСТРОЙКИ ===========================
TELEGRAM_BOT_TOKEN = "7885799580:AAGjm32oplBcmnTeD_yn9Jk_bnv6FCHrEso"
USERSBOX_API_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJjcmVhdGVkX2F0IjoxNzM4Njk1ODAxLCJhcHBfaWQiOjE3Mzg2OTU4MDF9.FPr2zvRNMmeXxKTztE5T5Am0__kBh8hP_xdzlpGgre4"
USERSBOX_API_URL = "https://api.usersbox.ru/v1"

ADMIN_ID = 5397898619
STATE_PASSWORD = 1
password = "Work2025"
skip_password_mode = True

activated_users = {}
COST_SEARCH = 2.5
COST_DB_SEARCH = 0.1

# Ограничение вывода в чат (2000 символов)
MAX_CHAT_LENGTH = 1269

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# ====================== CSS ДЛЯ ПОЛНОГО ОТЧЁТА ======================
CSS_STYLES = """
:root {
    --logo-users: #001e50;
    --logo-box: #229ed9;
}
html {
    line-height: 1.5;
    -webkit-text-size-adjust: 100%;
    font-family: ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont,
    Segoe UI, Roboto, Helvetica Neue, Arial, sans-serif;
}
body {
    margin: 0;
    padding: 0;
    background-color: #f7f8fa;
}
.container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 16px;
}
.header {
    background: #fff;
    border-bottom: 1px solid #ddd;
    padding: 10px;
    display: flex;
    align-items: center;
}
.header_logo {
    margin-right: 20px;
}
.header_title {
    font-size: 24px;
    font-weight: bold;
    margin-right: 20px;
}
.header_query span {
    display: inline-block;
    margin-right: 8px;
    font-weight: bold;
}
.header_print_button {
    margin-left: auto;
    cursor: pointer;
    background: none;
    border: none;
}
.navigation {
    position: relative;
}
.navigation_sticky {
    position: sticky;
    top: 0;
}
.navigation_ul {
    list-style: none;
    margin: 0;
    padding: 0;
}
.navigation_ul li {
    margin: 0 0 8px 0;
}
.db_header {
    background-color: #fff;
    padding: 8px;
    font-weight: bold;
    border: 1px solid #ddd;
    margin-bottom: 4px;
}
.db_cards {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    margin-bottom: 24px;
}
.card {
    background-color: #fff;
    border: 1px solid #ddd;
    padding: 8px;
    width: 300px;
    border-radius: 4px;
}
.row {
    display: flex;
    margin-bottom: 4px;
}
.row_left {
    min-width: 100px;
    font-weight: bold;
}
.row_right {
    flex-grow: 1;
    margin-left: 8px;
}
"""

# ===================== Расширенный словарь перевода =====================
translation_map = {
    "accounts": "Банковские счета",
    "account_number": "Номер счета",
    "cards": "Карты",
    "birth_date": "Дата рождения",
    "contacts": "Контакты",
    "full_name": "ФИО",
    "first_name": "Имя",
    "gender": "Пол",
    "home_phone": "Домашний телефон",
    "insurance_company": "Страховая компания",
    "insurance_policy": "Страховой полис",
    "insurance_policy_date": "Дата полиса",
    "last_name": "Фамилия",
    "middle_name": "Отчество",
    "permanent_address": "Постоянный адрес",
    "phone": "Телефон",
    "price": "Цена",
    "creation_time": "Время создания",
    "uuid_sberbank": "UUID Сбербанка",
    "comment": "Комментарий",
    "screen_name": "Имя пользователя",
    "can_access_closed": "Доступ к закрытым",
    "followers_count": "Количество подписчиков",
    "client": "Клиент",
    "code_podr": "Код подразделения",
    "document_number": "Номер документа",
    "document_serie": "Серия документа",
    "document_series": "Серия документа",
    "given_by": "Кем выдан",
    "given_date": "Дата выдачи",
    "internal_id": "Внутренний ID",
    "okato_code": "Код ОКАТО",
    "oktmo_code": "Код ОКТМО",
    "place_of_birth": "Место рождения",
    "address_2": "Адрес",
    "document_issue_date": "Дата выдачи документа",
    "neighborhood": "Район",
    "password": "Пароль",
    "base_type": "Тип базы",
    "body_no": "Номер кузова",
    "chassis_no": "Номер шасси",
    "color": "Цвет",
    "date": "Дата",
    "engine_no": "Номер двигателя",
    "engine_size": "Объем двигателя",
    "hp_power": "Мощность (л.с.)",
    "license_number": "Номер водительского удостоверения",
    "make": "Марка",
    "pts": "ПТС",
    "sts": "СТС",
    "system_number": "Системный номер",
    "vin": "VIN",
    "year_of_manufacture": "Год выпуска",
    "medpolis_date": "Дата медполиса",
    "medpolis_number": "Номер медполиса",
    "born_place": "Место рождения",
    "region": "Регион",
    "ru_mix.rosreestr_part_2024": "Россреестр (часть 2024)",
    "actual_address": "Фактический адрес",
    "pickup_point": "Пункт выдачи",
    "contact_person": "Контактное лицо",
    "names": "Имена",
    "city": "Город",
    "creation_date": "Дата создания",
    "update_date": "Дата обновления",
    "status": "Статус",
    "verified": "Проверен",
    "sex": "Пол",
    "monday": "понедельник",
    "tuesday": "вторник",
    "wednesday": "среда",
    "thursday": "четверг",
    "friday": "пятница",
    "saturday": "суббота",
    "sunday": "воскресенье"
}

# ===================== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ =====================
def safe_str_for_output(value) -> str:
    if isinstance(value, (dict, list)):
        val_str = json.dumps(value, ensure_ascii=False)
    else:
        val_str = str(value)
    return escape(val_str)

def usersbox_request(method: str, endpoint: str, params: dict = None) -> dict:
    url = f"{USERSBOX_API_URL}{endpoint}"
    headers = {"Authorization": USERSBOX_API_TOKEN}
    resp = requests.request(method, url, headers=headers, params=params)
    resp.raise_for_status()
    return resp.json()

def get_app_info() -> dict:
    r = usersbox_request("GET", "/getMe")
    if r.get("status") == "success":
        return r["data"]
    else:
        raise ValueError(f"Ошибка getMe: {r.get('error')}")

def usersbox_sources_map() -> dict:
    r = usersbox_request("GET", "/sources")
    mapping = {}
    if r.get("status") == "success":
        data = r["data"]
        items = data.get("items", [])
        for s in items:
            db = s["database"]
            coll = s["collection"]
            title = s.get("title") or f"{db}/{coll}"
            mapping[(db, coll)] = title
    return mapping

def try_parse_phone(s: str) -> bool:
    s_stripped = s.strip()
    if s_stripped.startswith("+"):
        try:
            phonenumbers.parse(s_stripped, None)
            return True
        except Exception:
            return False
    else:
        if s_stripped.isdigit() and len(s_stripped) in (10, 11):
            try:
                phonenumbers.parse("+" + s_stripped, None)
                return True
            except Exception:
                return False
    return False

def get_phone_info(s: str) -> dict:
    info = {
        "phone": s,
        "country": "неизвестно",
        "region": "неизвестно",
        "operator": "неизвестно"
    }
    parsed = None
    if s.startswith("+"):
        try:
            parsed = phonenumbers.parse(s, None)
        except Exception:
            pass
    if not parsed:
        if s.isdigit() and len(s) in (10, 11):
            s_plus = "+" + s
            try:
                parsed = phonenumbers.parse(s_plus, None)
                if parsed:
                    info["phone"] = s_plus
            except Exception:
                pass
    if parsed:
        ctry = geocoder.country_name_for_number(parsed, "ru")
        if ctry:
            info["country"] = ctry
        reg = geocoder.description_for_number(parsed, "ru")
        if reg:
            info["region"] = reg
        op = carrier.name_for_number(parsed, "ru")
        if op:
            info["operator"] = op
    return info

def format_phone_info(info: dict) -> str:
    phone_escaped = escape(info["phone"])
    return (
        "📱 \n"
        f"├ Телефон: ` {phone_escaped} `\n"
        f"├ Страна: ` {escape(info['country'])} `\n"
        f"├ Регион: ` {escape(info['region'])} `\n"
        f"└ Оператор: ` {escape(info['operator'])} `"
    )

def parse_advanced_query(user_query: str) -> str:
    parts = user_query.split()
    date_str = ""
    phone_list = []
    other_tokens = []
    for p in parts:
        if try_parse_phone(p):
            phone_list.append(p)
        elif re.match(r'^\d{1,2}\.\d{1,2}\.\d{4}$', p):
            date_str = p
        else:
            other_tokens.append(p)
    if len(other_tokens) > 3:
        fio_parts = other_tokens[:3]
        region_city = other_tokens[3:]
    elif len(other_tokens) == 3:
        fio_parts = other_tokens
        region_city = []
    else:
        fio_parts = []
        region_city = other_tokens
    tokens = []
    if region_city:
        tokens.append(" ".join(region_city))
    if fio_parts:
        tokens.append(" ".join(fio_parts))
    if date_str:
        tokens.append(date_str)
    if phone_list:
        tokens.extend(phone_list)
    if not tokens:
        return user_query
    return " ".join(tokens)

def is_relevant_query(q: str) -> bool:
    qs = q.strip()
    if len(qs) < 4:
        return False
    if try_parse_phone(qs):
        return True
    if "@" in qs and "." in qs:
        return True
    if qs.isdigit() and len(qs) in (10, 12):
        return True
    parts = qs.split()
    if len(parts) == 3 and all(p.isalpha() for p in parts):
        return True
    if qs.startswith("@") and len(qs) > 4:
        return True
    if len(parts) == 4:
        if all(p.isalpha() for p in parts):
            return True
        if all(x.isalpha() for x in parts[:3]) and re.match(r'^\d{1,2}\.\d{1,2}\.\d{4}$', parts[3]):
            return True
    return False

def create_html_report(query: str, items: list, src_map: dict) -> str:
    nav_items = []
    db_sections = []
    for source_obj in items:
        db = source_obj.get("source", {}).get("database", "unknown")
        coll = source_obj.get("source", {}).get("collection", "unknown")
        title = src_map.get((db, coll), f"{db}/{coll}")
        safe_id = re.sub(r'\W+', '_', f"{db}_{coll}")
        nav_items.append(
            f'<li><a href="#{safe_id}" class="navigation_link">{escape(title)}</a></li>'
        )
        section_lines = []
        section_lines.append(f'<div class="db" id="{safe_id}">')
        section_lines.append(f'  <div class="db_header">{escape(title)}</div>')
        section_lines.append('  <div class="db_cards">')
        docs = source_obj.get("hits", {}).get("items", [])
        for doc in docs:
            section_lines.append('    <div class="card">')
            for key in sorted(doc.keys()):
                if key.startswith("_"):
                    continue
                val_str = safe_str_for_output(doc[key])
                section_lines.append(
                    '      <div class="row">'
                    f'<div class="row_left">{escape(key)}</div>'
                    f'<div class="row_right">` {val_str} `</div></div>'
                )
            section_lines.append('    </div>')
        section_lines.append('  </div>')
        section_lines.append('</div>')
        db_sections.append("\n".join(section_lines))
    nav_html = "\n".join(nav_items)
    db_html = "\n".join(db_sections)
    full_html = f"""<!DOCTYPE html>
<html lang="ru">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Отчёт</title>
  <style>
{CSS_STYLES}
  </style>
</head>
<body>
  <header class="header">
    <div class="header_logo">
      <svg viewBox="0 0 506 76" class="h-4" width="120" style="display:block;">
        <path fill="var(--logo-users)" d="M267.768 33.405c-...Z"></path>
        <path fill="var(--logo-box)" d="M505.97 74.305h-...Z"></path>
      </svg>
    </div>
    <div class="header_title">Отчёт</div>
    <div class="header_query">
      <span>Запрос:</span>
      <span>{escape(query)}</span>
    </div>
    <button class="header_print_button" onclick="window.print()">
      🖨 Печать
    </button>
  </header>
  <div class="container content">
    <aside class="navigation">
      <div class="navigation_sticky">
        <h3>Навигация</h3>
        <ul class="navigation_ul">
{nav_html}
        </ul>
      </div>
    </aside>
    <main style="margin-top:20px;">
{db_html}
    </main>
  </div>
</body>
</html>
"""
    return full_html

def format_report_text(items: list) -> str:
    """
    Генерирует короткий текстовый отчёт в формате:
    ` ФИО ` ` Организация `
    """
    lines = []
    for source_obj in items:
        docs = source_obj.get("hits", {}).get("items", [])
        for doc in docs:
            full_name = doc.get("full_name", "").strip()
            org_name = doc.get("name", "").strip()
            if full_name and org_name:
                lines.append(f"` {full_name} ` ` {org_name} `")
            elif full_name:
                lines.append(f"` {full_name} `")
            elif org_name:
                lines.append(f"` {org_name} `")
    return "\n".join(lines)

def create_categories_lines(items: list) -> list:
    """
    Возвращает список строк с категориями (лицами, датами рождения, автомобилями, телефонами, ИНН, e-mail),
    где значения обрамлены обратными кавычками с пробелами.
    """
    lines = []
    faces = set()
    births = set()
    cars = set()
    phones = set()
    inns = set()
    emails = set()
    for source_obj in items:
        docs = source_obj.get("hits", {}).get("items", [])
        for doc in docs:
            if "fio" in doc:
                faces.add(str(doc["fio"]))
            else:
                sur = doc.get("surname")
                nm = doc.get("name")
                mid = doc.get("middle_name")
                if sur or nm or mid:
                    combined = " ".join(x for x in [sur, nm, mid] if x)
                    if combined.strip():
                        faces.add(combined.strip())
            if "birth_date" in doc:
                births.add(str(doc["birth_date"]))
            if "car_number" in doc:
                val = doc["car_number"]
                if isinstance(val, list):
                    for c in val:
                        cars.add(str(c))
                else:
                    cars.add(str(val))
            if "phones" in doc and isinstance(doc["phones"], list):
                for p in doc["phones"]:
                    phones.add(str(p))
            if "phone" in doc:
                val = doc["phone"]
                if isinstance(val, list):
                    for p in val:
                        phones.add(str(p))
                else:
                    phones.add(str(val))
            if "inn" in doc:
                val = doc["inn"]
                if isinstance(val, list):
                    for i in val:
                        inns.add(str(i))
                else:
                    inns.add(str(val))
            if "email" in doc:
                val = doc["email"]
                if isinstance(val, list):
                    for em in val:
                        emails.add(str(em))
                else:
                    emails.add(str(val))
            if "emails" in doc and isinstance(doc["emails"], list):
                for em in doc["emails"]:
                    emails.add(str(em))
    if faces:
        lines.append("👳‍  Лица:")
        flist = sorted(faces)
        for i, val in enumerate(flist):
            prefix = "└" if i == len(flist) - 1 else "├"
            lines.append(f"{prefix}` {escape(val)} `")
        lines.append("")
    if births:
        lines.append("🎉  Даты рождения:")
        blist = sorted(births)
        for i, val in enumerate(blist):
            prefix = "└" if i == len(blist) - 1 else "├"
            lines.append(f"{prefix}` {escape(val)} `")
        lines.append("")
    if cars:
        lines.append("🚘  Автомобили:")
        clist = sorted(cars)
        for i, val in enumerate(clist):
            prefix = "└" if i == len(clist) - 1 else "├"
            lines.append(f"{prefix}` {escape(val)} `")
        lines.append("")
    if phones:
        lines.append("📱  Телефоны:")
        plist = sorted(phones)
        for i, val in enumerate(plist):
            prefix = "└" if i == len(plist) - 1 else "├"
            lines.append(f"{prefix}` {escape(val)} `")
        lines.append("")
    if inns:
        lines.append("🏛  ИНН:")
        ilist = sorted(inns)
        for i, val in enumerate(ilist):
            prefix = "└" if i == len(ilist) - 1 else "├"
            lines.append(f"{prefix}` {escape(val)} `")
        lines.append("")
    if emails:
        lines.append("✉  Электронные почты:")
        elist = sorted(emails)
        for i, val in enumerate(elist):
            prefix = "└" if i == len(elist) - 1 else "├"
            lines.append(f"{prefix}` {escape(val)} `")
        lines.append("")
    return lines

def create_sources_lines(items: list, src_map: dict) -> list:
    """
    Формирует список строк по источникам. Если значение поля – словарь,
    то выводится вложенная структура.
    """
    lines = []
    for source_obj in items:
        db = source_obj.get("source", {}).get("database", "unknown")
        coll = source_obj.get("source", {}).get("collection", "unknown")
        title = src_map.get((db, coll), f"{db}/{coll}")
        docs = source_obj.get("hits", {}).get("items", [])
        if not docs:
            continue
        icon = "🗄"
        low_t = title.lower()
        if "фомс" in low_t:
            icon = "🏥"
        elif "жители" in low_t:
            icon = "🏠"
        elif "cdek" in low_t or "авто" in low_t:
            icon = "🚚"
        lines.append(f"{icon} {escape(title)}:")
        for doc_i, doc in enumerate(docs, start=1):
            # Используем разные префиксы для первого и последующих ключей
            doc_keys = sorted(k for k in doc.keys() if not k.startswith("_"))
            for idx, k in enumerate(doc_keys):
                prefix = "├" if idx < len(doc_keys)-1 else "└"
                val = doc[k]
                # Если значение является словарём, форматируем вложенно
                if isinstance(val, dict):
                    lines.append(f"{prefix} {escape(k)}:")
                    sub_keys = list(val.keys())
                    for sub_idx, sub_key in enumerate(sub_keys):
                        sub_prefix = "├" if sub_idx < len(sub_keys)-1 else "└"
                        sub_val = val[sub_key]
                        lines.append(f"│ {sub_prefix} {escape(sub_key)}: ` {escape(str(sub_val))} `")
                elif isinstance(val, list):
                    joined = ", ".join(str(item) for item in val)
                    lines.append(f"{prefix} {escape(k)}: ` {escape(joined)} `")
                else:
                    lines.append(f"{prefix} {escape(k)}: ` {escape(str(val))} `")
        lines.append("")
    return lines

# ===================== ОБРАБОТЧИК ОШИБОК =====================
async def error_handler(update: object, context: CallbackContext) -> None:
    try:
        raise context.error
    except Forbidden as e:
        logging.warning(f"Forbidden error: {e}. Бот заблокирован/выгнан.")
    except Exception as e:
        logging.error(f"Произошла ошибка: {e}", exc_info=True)

# ===================== ХЕНДЛЕРЫ КОМАНД =====================
async def help_command(update: Update, context: CallbackContext):
    text = (
        "Доступные команды:\n"
        "/start — запуск бота\n"
        "/balance — проверить баланс\n"
        "/supports — контакты саппорта\n"
        "/getme — информация о приложении\n"
        "/explain <запрос>\n"
        "/short — короткий отчёт по запросу\n\n"
        "Отправьте ФИО, телефон, e-mail, ИНН для поиска."
    )
    await update.message.reply_text(text, parse_mode="HTML")

async def cmd_start(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if skip_password_mode:
        activated_users[user_id] = True
        await show_main_menu(update)
        return ConversationHandler.END
    if activated_users.get(user_id, False):
        await show_main_menu(update)
        return ConversationHandler.END
    await update.message.reply_text("Для активации бота введите пароль:", parse_mode="HTML")
    return STATE_PASSWORD

async def password_handler(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    entered = update.message.text.strip()
    if skip_password_mode:
        activated_users[user_id] = True
        await show_main_menu(update)
        return ConversationHandler.END
    if entered == password:
        activated_users[user_id] = True
        await show_main_menu(update)
    else:
        await update.message.reply_text(
            "Съебал отсюда халявщик! За покупкой к @alekseybalagura",
            parse_mode="HTML"
        )
    return ConversationHandler.END

async def show_main_menu(update: Update):
    text = (
        "👋 <b>Привет от Alladina! Фарту и тотала!</b>\n\n"
        "Доступные команды:\n"
        "/balance — проверить баланс\n"
        "/supports — контакты саппорта\n"
        "/getme — информация о приложении\n"
        "/explain — показать только кол-во документов\n"
        "/short — короткий отчёт\n"
        "/help — помощь\n\n"
        "Просто отправьте ФИО, телефон, e-mail, ИНН для поиска."
    )
    kb = [
        [KeyboardButton("/balance"), KeyboardButton("/supports")],
        [KeyboardButton("/getme"), KeyboardButton("/explain")],
        [KeyboardButton("/short"), KeyboardButton("/help")]
    ]
    markup = ReplyKeyboardMarkup(kb, resize_keyboard=True)
    await update.message.reply_text(text, parse_mode="HTML", reply_markup=markup)

async def check_activation(update: Update) -> bool:
    user_id = update.effective_user.id
    if skip_password_mode:
        return True
    if user_id not in activated_users or not activated_users[user_id]:
        await update.message.reply_text("Вы не активированы. Используйте /start.", parse_mode="HTML")
        return False
    return True

async def supports_command(update: Update, context: CallbackContext):
    if not await check_activation(update):
        return
    msg = (
        "<b>Контакты:</b>\n"
        "Создатель: @alekseybalagura\n"
        "Саппорт: @WorkerBro666"
    )
    await update.message.reply_text(msg, parse_mode="HTML")

async def getme_command(update: Update, context: CallbackContext):
    if not await check_activation(update):
        return
    try:
        data = get_app_info()
        txt = (
            f"ID приложения: {data['_id']}\n"
            f"Название: {data['title']}\n"
            f"Баланс: {data['balance']} ₽\n"
            f"Активен: {data['is_active']}"
        )
    except Exception as e:
        txt = f"Ошибка /getme: {e}"
    await update.message.reply_text(txt, parse_mode="HTML")

async def explain_command(update: Update, context: CallbackContext):
    if not await check_activation(update):
        return
    if not context.args:
        await update.message.reply_text("Использование: /explain <запрос>", parse_mode="HTML")
        return
    query = " ".join(context.args)
    try:
        params = {"q": query}
        r = usersbox_request("GET", "/explain", params=params)
        if r.get("status") == "success":
            data = r["data"]
            cnt = data.get("count", 0)
            if cnt == 0:
                txt = f"По запросу '{query}' ничего не найдено."
            else:
                txt = f"Найдено всего документов: {cnt}\n(Без вывода данных.)"
        else:
            err = r.get("error", {})
            txt = f"Ошибка /explain: {err}"
    except Exception as e:
        txt = f"Произошла ошибка: {e}"
    await update.message.reply_text(txt, parse_mode="HTML")

async def balance_command(update: Update, context: CallbackContext):
    if not await check_activation(update):
        return
    try:
        data = get_app_info()
        bal = data.get("balance", 0.0)
        possible_search = int(bal // COST_SEARCH)
        lines = [
            f"Текущий баланс: {bal} ₽\n",
            f" — На Мамонтёнков осталось ~ {possible_search} запрос(ов)\n",
        ]
        if possible_search == 0:
            lines.append("\nА всё бомжи, над раньше было!!")
        elif possible_search <= 100 and (possible_search % 10 == 0):
            lines.append(
                f"\nОсталось {possible_search} запросов!\n"
                f"Для пополнения пишите @WorkerBro666, либо @alekseybalagura! Фарту!!"
            )
        else:
            lines.append(
                "\n— Для пополнения пишите @WorkerBro666, либо @alekseybalagura! Фарту!!"
            )
        txt = "".join(lines)
    except Exception as e:
        txt = f"Ошибка /balance: {e}"
    await update.message.reply_text(txt, parse_mode="HTML")

async def admin_command(update: Update, context: CallbackContext):
    global password, skip_password_mode
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        await update.message.reply_text("У вас нет доступа к /admin.", parse_mode="HTML")
        return
    args = context.args
    if not args:
        txt = (
            "Доступные команды /admin:\n"
            "• /admin list\n"
            "• /admin remove user_id\n"
            "• /admin clear\n"
            "• /admin setpass новыйПароль\n"
            "• /admin nopass\n"
            "• /admin passmode\n"
        )
        await update.message.reply_text(txt, parse_mode="HTML")
        return
    cmd = args[0].lower()
    if cmd == "list":
        if not activated_users:
            await update.message.reply_text("Нет активированных пользователей.", parse_mode="HTML")
            return
        lines = ["Активированные user_id:"]
        for uid in activated_users:
            lines.append(f"- {uid}")
        lines.append("\nЧтобы снять доступ: /admin remove user_id")
        text_list = "\n".join(lines)
        await update.message.reply_text(text_list, parse_mode="HTML")
    elif cmd == "remove":
        if len(args) < 2:
            await update.message.reply_text("Использование: /admin remove user_id", parse_mode="HTML")
            return
        try:
            remove_id = int(args[1])
        except ValueError:
            await update.message.reply_text("user_id должен быть числом.", parse_mode="HTML")
            return
        if remove_id in activated_users:
            del activated_users[remove_id]
            await update.message.reply_text(f"Пользователь {remove_id} удалён.", parse_mode="HTML")
        else:
            await update.message.reply_text(f"Пользователь {remove_id} не найден.", parse_mode="HTML")
    elif cmd == "clear":
        activated_users.clear()
        await update.message.reply_text("Все пользователи сброшены.", parse_mode="HTML")
    elif cmd == "setpass":
        if len(args) < 2:
            await update.message.reply_text("Использование: /admin setpass новыйПароль", parse_mode="HTML")
            return
        newpass = args[1].strip()
        password = newpass
        activated_users.clear()
        skip_password_mode = False
        await update.message.reply_text(
            f"Пароль изменён на '{newpass}'. Все пользователи сброшены. Парольный режим включён.",
            parse_mode="HTML"
        )
    elif cmd == "nopass":
        skip_password_mode = True
        activated_users.clear()
        await update.message.reply_text("Пароль отключён. Все могут использовать бота без активации.", parse_mode="HTML")
    elif cmd == "passmode":
        skip_password_mode = False
        activated_users.clear()
        await update.message.reply_text("Режим пароля включён. Все пользователи сброшены. Им нужен пароль.", parse_mode="HTML")
    else:
        await update.message.reply_text(
            "Неизвестная подкоманда /admin (list, remove, clear, setpass, nopass, passmode).",
            parse_mode="HTML"
        )

# ============ ОБРАБОТЧИК ТЕКСТОВОГО ПОИСКА (ДЕТАЛЬНЫЙ) ============
async def detailed_text_search_handler(update: Update, context: CallbackContext):
    if not activated_users.get(update.effective_user.id, False):
        await update.message.reply_text("Вы не активированы. Используйте /start.", parse_mode="HTML")
        return
    user_query = update.message.text.strip()
    q = parse_advanced_query(user_query)
    if not is_relevant_query(q):
        await update.message.reply_text(
            "Похоже, это обычное сообщение. Я обрабатываю только:\n"
            "- телефон (с + или без)\n"
            "- e-mail\n"
            "- ИНН (10/12 цифр)\n"
            "- ФИО (3 слова)\n"
            "- ФИО + дата рождения (4 слова)\n"
            "- @username",
            parse_mode="HTML"
        )
        return
    phone_msg = ""
    ph_info = get_phone_info(q)
    if ph_info["operator"] != "неизвестно":
        phone_msg = format_phone_info(ph_info)
    try:
        params = {"q": q}
        result = usersbox_request("GET", "/search", params=params)
        if result.get("status") != "success":
            err = result.get("error", {})
            await update.message.reply_text(f"Ошибка /search: {err}", parse_mode="HTML")
            return
        data = result.get("data", {})
        total_sources = data.get("count", 0)
        items = data.get("items", [])
        total_docs = sum(s.get("hits", {}).get("count", 0) for s in items)
        if total_docs == 0 or total_sources == 0:
            if phone_msg:
                await update.message.reply_text(
                    phone_msg + "\n\n😔 В наших источниках ничего не найдено",
                    parse_mode="HTML"
                )
            else:
                await update.message.reply_text("😔 В наших источниках ничего не найдено", parse_mode="HTML")
            return
        lines = []
        if phone_msg:
            lines.extend(phone_msg.split("\n"))
            lines.append("")
        cat_lines = create_categories_lines(items)
        lines.extend(cat_lines)
        s_map = usersbox_sources_map()
        src_lines = create_sources_lines(items, s_map)
        lines.extend(src_lines)
        # Применяем перевод для всех ключей
        translated_lines = []
        for line in lines:
            for eng_key, rus_key in translation_map.items():
                line = line.replace(eng_key, rus_key)
            translated_lines.append(line)
        final_text = "\n".join(translated_lines)
        if len(final_text) > MAX_CHAT_LENGTH:
            final_text = final_text[:MAX_CHAT_LENGTH] + "\n\n... (обрезано)"
        await update.message.reply_text(final_text, parse_mode="HTML")
        html_report = create_html_report(q, items, s_map)
        file_bytes = io.BytesIO(html_report.encode("utf-8"))
        file_bytes.name = "report.html"
        caption_html = (
            f"Найдено {total_docs} документов в {total_sources} источниках.\n"
            "Полный HTML-отчёт (откройте в браузере)."
        )
        await update.message.reply_document(document=file_bytes, filename="report.html", caption=caption_html)
    except Exception as e:
        await update.message.reply_text(f"Произошла ошибка: {e}", parse_mode="HTML")

# ============ ОБРАБОТЧИК ТЕКСТОВОГО ПОИСКА (КОРОТКИЙ) ============
async def short_text_search_handler(update: Update, context: CallbackContext):
    if not activated_users.get(update.effective_user.id, False):
        await update.message.reply_text("Вы не активированы. Используйте /start.", parse_mode="HTML")
        return
    user_query = update.message.text.strip()
    q = parse_advanced_query(user_query)
    if not is_relevant_query(q):
        await update.message.reply_text("⚠️ Некорректный запрос. Попробуйте снова.", parse_mode="HTML")
        return
    try:
        params = {"q": q}
        result = usersbox_request("GET", "/search", params=params)
        if result.get("status") != "success":
            await update.message.reply_text(f"Ошибка /search: {result.get('error')}", parse_mode="HTML")
            return
        items = result.get("data", {}).get("items", [])
        if not items:
            await update.message.reply_text("😔 В наших источниках ничего не найдено", parse_mode="HTML")
            return
        formatted_text = format_report_text(items)
        if len(formatted_text) > MAX_CHAT_LENGTH:
            formatted_text = formatted_text[:MAX_CHAT_LENGTH] + "\n\n... (обрезано)"
        await update.message.reply_text(formatted_text, parse_mode="MarkdownV2")
    except Exception as e:
        await update.message.reply_text(f"🚨 Ошибка: {e}", parse_mode="HTML")

# ============================= MAIN =============================
def main():
    application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", cmd_start)],
        states={
            STATE_PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, password_handler)]
        },
        fallbacks=[],
        allow_reentry=True
    )
    application.add_handler(conv_handler)
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("supports", supports_command))
    application.add_handler(CommandHandler("getme", getme_command))
    application.add_handler(CommandHandler("explain", explain_command))
    application.add_handler(CommandHandler("balance", balance_command))
    application.add_handler(CommandHandler("admin", admin_command))
    application.add_handler(CommandHandler("short", short_text_search_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, detailed_text_search_handler))
    application.add_error_handler(error_handler)
    application.run_polling()

if __name__ == "__main__":
    main()
