import telebot
from telebot import types, apihelper

import os
from datetime import datetime

import src.handlers as handlers

log_file = open("log.txt", "a+")

def log_error(text: str):
    print("\nERROR, details in log.txt\n")
    dt = datetime.now().strftime("%d.%m.%y %H:%M:%S")
    dt = dt[:dt.index(".")]
    log_file.write(dt + "\t" + text + "\n")
    log_file.flush()

if __name__ == "__main__":

    os.system("cls")

    print("Bot started")
    
    handlers.bot.polling(none_stop=True, interval=0)
    
    log_file.close()

    print("Bot stopped")
