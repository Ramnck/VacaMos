from email import message
import telebot
from telebot import types, apihelper
from src.api import Search
from db.logic import Database

import requests as req
import json
import settings

description = req.get("https://api.hh.ru/dictionaries").json()

bot = telebot.TeleBot(settings.SECRET_KEY)
search = Search()
db = Database()

users = {}

default_params = {"schedule" : "fullDay"}
schedule_params = [i["id"] for i in description["schedule"]]
currency_params = [i["code"] for i in description["currency"]]

Button = types.KeyboardButton
Keyboard = types.ReplyKeyboardMarkup

inl_Button = types.InlineKeyboardButton
inl_Keyboard = types.InlineKeyboardMarkup

remove_inline = types.ReplyKeyboardRemove

def find_handler(message : message.Message):
    # print("Ищу"+message.text)
    user_params = db.get_params(message.from_user.id)
    # print(user_params)
    vacancies = search.get_vacancies(message.text, **user_params)
    # print(vacancies)
    keyboard = inl_Keyboard()
    for vacancy in vacancies:
        keyboard.add(inl_Button(text=vacancy["name"], callback_data=vacancy["id"]))
    bot.send_message(message.chat.id, "Найденные вакансии:", reply_markup=keyboard)

def parameter_menu(message):
    bot.delete_message(message.chat.id, message.id)
    keyboard = inl_Keyboard()
    keyboard.add(inl_Button(text="График работы", callback_data="schedule"))
    keyboard.add(inl_Button(text="Примерная зарплата (тыс)", callback_data="salary"))
    keyboard.add(inl_Button(text="Зарплата обязательно указана", callback_data="only_with_salary"))
    keyboard.add(inl_Button(text="Валюта", callback_data="currency"))
    keyboard.add(inl_Button(text="Назад", callback_data="back"))
    bot.send_message(message.chat.id, "Параметры поиска:", reply_markup=keyboard)

def find_f(message):
    if str(message.from_user.id) not in users.keys():
        users[str(message.chat.id)] = default_params
    bot.send_message(message.chat.id, "Введите название")
    bot.register_next_step_handler(message, find_handler)

def only_with_salary_f(call):
    keyboard = inl_Keyboard()
    keyboard.add(
        inl_Button(text="Да", callback_data="True"),
        inl_Button(text="Нет", callback_data="False")
    )
    keyboard.add(inl_Button(text="Назад", callback_data="back_menu"))
    bot.send_message(call.message.chat.id, "Искать резюме только с указанной зарплатой?", reply_markup=keyboard)

def salary_f(call):
    keyboard = inl_Keyboard()
    keyboard.add(inl_Button(text="Назад", callback_data="back_menu"))
    bot.send_message(call.message.chat.id, "Укажите примерную зарплату в тысячах", reply_markup=keyboard)
    bot.register_next_step_handler(call.message, salary_value)

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
    parameter_menu(message)

def schedule_f(call):
    keyboard = inl_Keyboard()
    for i in description["schedule"]:
        keyboard.add(inl_Button(text=i["name"], callback_data=i["id"]))
    keyboard.add(inl_Button(text="Назад", callback_data="back_menu"))
    bot.send_message(call.message.chat.id, "Укажите график работы", reply_markup=keyboard)

def currency_f(call):
    keyboard = inl_Keyboard()
    for i in description["currency"]:
        keyboard.add(inl_Button(text=i["name"], callback_data=i["code"]))
    keyboard.add(inl_Button(text="Назад", callback_data="back_menu"))
    bot.send_message(call.message.chat.id, "Укажите график работы", reply_markup=keyboard)

functions = {
    "поиск": find_f,
    "параметры поиска": parameter_menu,
    "schedule" : schedule_f, 
    "salary" : salary_f, 
    "only_with_salary" : only_with_salary_f, 
    "currency" : currency_f
}

@bot.callback_query_handler(func=lambda call: call.data in schedule_params)
def schedule_value(call):
    db.set_param(call.message.chat.id, "schedule", call.data)
    parameter_menu(call.message)

@bot.callback_query_handler(func=lambda call: call.data in currency_params)
def currency_value(call):
    db.set_param(call.message.chat.id, "currency", call.data)
    parameter_menu(call.message)

@bot.callback_query_handler(func=lambda call: call.data in ["True", "False"])
def only_with_salary_value(call):
    db.set_param(call.message.chat.id, "only_with_salary", bool(call.data))
    parameter_menu(call.message)

@bot.callback_query_handler(func=lambda call: "back" in call.data)
def back(call):
    if call.data == "back_menu":
        parameter_menu(call.message)
        return
    try:
        functions[call.data[call.data.index("_")+1:]](call)
    except ValueError:
        menu_keyboard = Keyboard(resize_keyboard=True, one_time_keyboard=True)
        menu_keyboard.add(Button("Поиск"),Button("Параметры поиска"))
        bot.delete_message(call.message.chat.id, call.message.id)
        bot.send_message(call.message.chat.id, "Выберите действие", parse_mode='html', reply_markup=menu_keyboard)

@bot.callback_query_handler(func=lambda call: call.data in ["schedule", "salary", "only_with_salary", "currency"])
def parameter_choose(call):
    keyboard = inl_Keyboard()
    bot.delete_message(call.message.chat.id, call.message.id)
    functions[call.data](call)
    # bot.send_message(call.message.chat.id, "Введите значение")

@bot.callback_query_handler(func=lambda call: str(call.data).isdigit())
def vacancy_handler(call):
    vacancy = search.get_vacancy(int(call.data))
    salary = ""
    if "from" in vacancy["salary"].keys():
        salary += "От "
        salary += str(vacancy["salary"]["from"])
    if "to" in vacancy["salary"].keys() and vacancy["salary"]["to"] != None:
        salary += " До "
        salary += str(vacancy["salary"]["to"])
    if "currency" in vacancy["salary"].keys():
        salary += " "
        salary += vacancy["salary"]["currency"]

    description = vacancy["description"]
    
    if len(description) > 300:
        description = description[:300] + "..."

    output = f"""{vacancy["name"]}
    Описание:
    {description}
    Зарплата: {salary}
    """
    keyboard = inl_Keyboard()
    keyboard.add(inl_Button("Вакансия", url=vacancy["url"]))
    bot.send_message(call.message.chat.id, output, reply_markup=keyboard)

@bot.message_handler(commands=["start"])
def welcome_handler(message):
    db.create_user(message.from_user.id)
    start_message = f"Добро пожаловать, {message.from_user.first_name}!\nЯ - <b>{bot.get_me().first_name}</b>, бот созданный помочь вам с поиском работы."
    keyboard = Keyboard(resize_keyboard=True, one_time_keyboard=True)
    keyboard.add(Button("Поиск"),Button("Параметры поиска"))
    bot.send_message(message.chat.id, start_message, parse_mode='html', reply_markup=keyboard)

@bot.message_handler(commands=["stop"])
def stop(message):
    db.delete_user(message.from_user.id)

@bot.message_handler(content_types=["text"])
def text_handler(message):
    if message.text.lower() in functions.keys():
        functions[message.text.lower()](message)