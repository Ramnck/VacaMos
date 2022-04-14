from email import message
import telebot
from telebot import types, apihelper

import requests as req
import json
import re

import settings
from src.api import Search
from db.logic import Database

bot = telebot.TeleBot(settings.SECRET_KEY)
search = Search()
db = Database()
cleanre = re.compile('<.*?>')

description = req.get("https://api.hh.ru/dictionaries").json()
schedule_params = [i["id"] for i in description["schedule"]]
currency_params = [i["code"] for i in description["currency"]]

Button = types.KeyboardButton
Keyboard = types.ReplyKeyboardMarkup
inl_Button = types.InlineKeyboardButton
inl_Keyboard = types.InlineKeyboardMarkup

def parameter_menu_f(message):
    bot.delete_message(message.chat.id, message.id-1)
    bot.delete_message(message.chat.id, message.id)
    keyboard = inl_Keyboard()
    keyboard.add(inl_Button(text="График работы", callback_data="schedule"))
    keyboard.add(inl_Button(text="Примерная зарплата (тыс)", callback_data="salary"))
    keyboard.add(inl_Button(text="Зарплата обязательно указана", callback_data="only_with_salary"))
    keyboard.add(inl_Button(text="Валюта", callback_data="currency"))
    keyboard.add(inl_Button(text="Назад", callback_data="back"))
    bot.send_message(message.chat.id, "Параметры поиска:", reply_markup=keyboard)

def find_f(message):
    bot.delete_message(message.chat.id, message.id)
    bot.delete_message(message.chat.id, message.id-1)
    keyboard = inl_Keyboard()
    keyboard.add(inl_Button(text="Назад", callback_data="back"))
    bot.send_message(message.chat.id, "Введите название", reply_markup=keyboard)
    bot.register_next_step_handler(message, find_handler)

def only_with_salary_f(call):
    keyboard = inl_Keyboard()
    keyboard.add(
        inl_Button(text="Да", callback_data="True"),
        inl_Button(text="Нет", callback_data="False")
    )
    keyboard.add(inl_Button(text="Назад", callback_data="back_menu_handler"))
    bot.send_message(call.message.chat.id, "Искать резюме только с указанной зарплатой?", reply_markup=keyboard)

def salary_f(call):
    keyboard = inl_Keyboard()
    keyboard.add(inl_Button(text="Назад", callback_data="back_menu_handler"))
    bot.send_message(call.message.chat.id, "Укажите примерную зарплату в тысячах", reply_markup=keyboard)
    bot.register_next_step_handler(call.message, salary_value)

def schedule_f(call):
    keyboard = inl_Keyboard()
    for i in description["schedule"]:
        keyboard.add(inl_Button(text=i["name"], callback_data=i["id"]))
    keyboard.add(inl_Button(text="Назад", callback_data="back_menu_handler"))
    bot.send_message(call.message.chat.id, "Укажите график работы", reply_markup=keyboard)

def currency_f(call):
    keyboard = inl_Keyboard()
    for i in description["currency"]:
        keyboard.add(inl_Button(text=i["name"], callback_data=i["code"]))
    keyboard.add(inl_Button(text="Назад", callback_data="back_menu_handler"))
    bot.send_message(call.message.chat.id, "Укажите график работы", reply_markup=keyboard)

functions = {
    "поиск": find_f,
    "параметры поиска": parameter_menu_f,
    "schedule" : schedule_f, 
    "salary" : salary_f, 
    "only_with_salary" : only_with_salary_f, 
    "currency" : currency_f
}

def find_handler(message : message.Message):
    user_params = db.get_params(message.chat.id)
    vacancies = search.get_vacancies(message.text, **user_params)
    try:
        bot.send_message(message.chat.id, vacancies["error"])
        menu_handler(message)
        return        
    except Exception:
        pass
    keyboard = inl_Keyboard()
    output = ""
    if len(vacancies) > 0:    
        for vacancy in vacancies:
            keyboard.add(inl_Button(text=vacancy["name"], callback_data=vacancy["id"]))
        keyboard.add(inl_Button(text="Ещё", callback_data="more"))
        output = f"Вакансии по запросу {message.text}:"
    else:
        output = f"Вакансий по запросу {message.text} не найдено"
        keyboard.add(inl_Button(text="Повторить поиск", callback_data="find"))
    bot.delete_message(message.chat.id, message.id)
    bot.delete_message(message.chat.id, message.id-1)
    keyboard.add(inl_Button(text="Назад", callback_data="back"))   
    bot.send_message(message.chat.id, output, reply_markup=keyboard)

@bot.callback_query_handler(func=lambda call: call.data == "find")
def find(call):
    bot.delete_message(call.message.chat.id, call.message.id)
    keyboard = inl_Keyboard()
    keyboard.add(inl_Button(text="Назад", callback_data="back"))
    bot.send_message(call.message.chat.id, "Введите название", reply_markup=keyboard)
    bot.register_next_step_handler(call.message, find_handler)

@bot.callback_query_handler(func=lambda call: call.data=="more")
def more(call):
    bot.delete_message(call.message.chat.id, call.message.id)
    message = call.message
    message.text = message.text[20:-1]
    find_handler(message)

@bot.callback_query_handler(func=lambda call: "back" in call.data)
def back(call):
    bot.clear_step_handler_by_chat_id(chat_id=call.message.chat.id)
    if call.data == "back_menu_handler":
        parameter_menu_f(call.message)
        return
    try:
        functions[call.data[call.data.index("_")+1:]](call)
    except ValueError:
        menu_handler_keyboard = Keyboard(resize_keyboard=True, one_time_keyboard=True)
        menu_handler_keyboard.add(Button("Поиск"),Button("Параметры поиска"))
        bot.delete_message(call.message.chat.id, call.message.id)
        bot.send_message(call.message.chat.id, "Выберите действие", parse_mode='html', reply_markup=menu_handler_keyboard)

@bot.callback_query_handler(func=lambda call: call.data in schedule_params)
def schedule_value(call):
    db.set_param(call.message.chat.id, "schedule", call.data)
    parameter_menu_f(call.message)

@bot.callback_query_handler(func=lambda call: call.data in currency_params)
def currency_value(call):
    db.set_param(call.message.chat.id, "currency", call.data)
    parameter_menu_f(call.message)

@bot.callback_query_handler(func=lambda call: call.data in ["True", "False"])
def only_with_salary_value(call):
    db.set_param(call.message.chat.id, "only_with_salary", bool(call.data))
    parameter_menu_f(call.message)

def salary_value(message):
    bot.delete_message(message.chat.id, message.id-1)
    nums = "1234567890"
    for i in message.text:
        if i not in nums:
            bot.send_message(message.chat.id, "Используйте только цифры")
            bot.delete_message(message.chat.id, message.id)
            bot.register_next_step_handler(message, salary_value)
            return
    db.set_param(message.chat.id, "salary", message.text)
    parameter_menu_f(message)

@bot.callback_query_handler(func=lambda call: call.data in ["schedule", "salary", "only_with_salary", "currency"])
def parameter_choose(call):
    keyboard = inl_Keyboard()
    bot.delete_message(call.message.chat.id, call.message.id)
    functions[call.data](call)

@bot.callback_query_handler(func=lambda call: str(call.data).isdigit())
def vacancy_handler(call):
    vacancy = search.get_vacancy(int(call.data))
    if "error" in vacancy.keys():
        bot.send_message(call.message.chat.id, vacancy["error"])
        menu_handler(call.message)
        return

    salary = ""

    if "from" in vacancy["salary"].keys():
        salary += f"<i>От</i> <b>{vacancy['salary']['from']}</b>"
    if "to" in vacancy["salary"].keys() and vacancy["salary"]["to"] != None:
        salary += f" <i>До</i> <b>{vacancy['salary']['to']}</b>"
    if "currency" in vacancy["salary"].keys():
        salary += f' <i>{vacancy["salary"]["currency"].lower()}</i>'

    if "from" not in vacancy["salary"].keys() and "to" not in vacancy["salary"].keys():
        salary = "Зарплата не указана"

    description = re.sub(cleanre, '', vacancy["description"])
    
    if len(description) > 300:
        description = description[:300] + "..."

    output = f"""<i><b>{vacancy["name"]}</b></i>
<u>Описание:</u>
{description}
<u>Зарплата:</u> {salary}"""
    keyboard = inl_Keyboard()
    keyboard.add(inl_Button("Вакансия", url=vacancy["url"]))
    bot.send_message(call.message.chat.id, output, reply_markup=keyboard, parse_mode='html',)

@bot.message_handler(commands=["start"])
def welcome_handler(message):
    db.create_user(message.from_user.id)
    start_message = f"Добро пожаловать, {message.from_user.first_name}!\nЯ - <b>{bot.get_me().first_name}</b>, бот созданный помочь вам с поиском работы."
    keyboard = Keyboard(resize_keyboard=True, one_time_keyboard=True)
    keyboard.add(Button("Поиск"),Button("Параметры поиска"))
    bot.send_message(message.chat.id, start_message, parse_mode='html', reply_markup=keyboard)

@bot.message_handler(commands=["menu"])
def menu_handler(message):
    menu_handler_keyboard = Keyboard(resize_keyboard=True, one_time_keyboard=True)
    menu_handler_keyboard.add(Button("Поиск"),Button("Параметры поиска"))
    bot.delete_message(message.chat.id, message.id)
    bot.send_message(message.chat.id, "Выберите действие", parse_mode='html', reply_markup=menu_handler_keyboard)

@bot.message_handler(commands=["stop"])
def stop_handler(message):
    db.delete_user(message.from_user.id)

@bot.message_handler(content_types=["text"])
def text_handler(message):
    if message.text.lower() in functions.keys():
        functions[message.text.lower()](message)
    else:
        menu_handler(message)