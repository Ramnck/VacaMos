import telebot
from telebot import types, apihelper

import os

import src.handlers as handlers

if __name__ == "__main__":

    os.system("cls")

    print("Bot started")
    
    handlers.bot.polling(none_stop=True, interval=0)
    
    print("Bot stopped")
