# -*- coding: utf-8 -*-

import json
import os

import requests
import schedule
import telebot
import time
import uuid
import pandas as pd

from threading import Thread

from psycopg2 import Binary
from psycopg2.extras import Json
from psycopg2.extensions import adapt

from telebot.types import ReplyKeyboardMarkup

from config import *
from telegram_bot_utils import *

telegram_bot = telebot.TeleBot(TELEGRAM_API_TOKEN)

catchable_signals = set()
threads = []
current_state_info_default = {}

main_menu_markup = InlineKeyboardMarkup()
main_menu_keyboard = ReplyKeyboardMarkup(resize_keyboard=True)


def initialization():
    global current_state_info_default

    current_state_info_default = {
        "referral_user_telegram_id": -1
    }


def signals_handler(sig, frame):
    global threads

    if sig == 2:
        for t in threads:
            Thread(target=t.join, daemon=True).start()

        write_log("EXIT")

        exit(0)


def check_and_update_tasks():
    with open("tasks.json", "r") as f:
        tasks = json.load(f)

    tasks_list = list(tasks)
    for task_id in tasks_list:
        print(task_id)

    with open('tasks.json', 'w') as f:
        json.dump(tasks, f, ensure_ascii=False, indent=4)


def threading_func_schedule_run_pending():
    schedule.every(1).seconds.do(check_and_update_tasks)
    while True:
        schedule.run_pending()
        time.sleep(1)


def transform_users_to_excel_table():
    users = execute_sql(
        "SELECT * "
        "FROM users",
        POSTGRES_CONNECTION_PARAMS
    )
    df = pd.DataFrame(users)
    df.to_excel("users.xlsx")


@telegram_bot.message_handler(func=lambda message: True, content_types=CONTENT_TYPES)
def message_handler(message):
    global telegram_bot

    write_log("MESSAGE" +
              " " +
              str(message.chat.id) +
              " " +
              str(message.from_user.id) +
              " " +
              str(message.from_user.username) +
              " " +
              str(message.text))

    user_telegram_id = message.from_user.id
    username = message.from_user.username

    if username is None:
        username = ""
    try:
        user = execute_sql(
            f"SELECT * "
            f"FROM users "
            f"WHERE telegram_id={user_telegram_id}",
            POSTGRES_CONNECTION_PARAMS
        )[0]
    except IndexError:
        execute_sql(
            f"INSERT into users(telegram_id, username, current_state_info) "
            f"VALUES ({user_telegram_id}, {adapt(username)}, {Json(current_state_info_default)})",
            POSTGRES_CONNECTION_PARAMS
        )
        user = execute_sql(
            f"SELECT * "
            f"FROM users "
            f"WHERE telegram_id={user_telegram_id}",
            POSTGRES_CONNECTION_PARAMS
        )[0]

    # TODO: add in db last usage

    user_current_state_info = user["current_state_info"]

    if message.text[:6] == "/start":
        try:
            referral_user_telegram_id = int(message.text[6:])
        except ValueError:
            referral_user_telegram_id = -1

        if user_current_state_info["referral_user_telegram_id"] == -1 and referral_user_telegram_id != -1:
            user_current_state_info["referral_user_telegram_id"] = referral_user_telegram_id
            # send goods to referral_user_telegram_id
            execute_sql(
                f"UPDATE users "
                f"SET current_state_info={Json(user_current_state_info)} "
                f"WHERE telegram_id={user_telegram_id}",
                POSTGRES_CONNECTION_PARAMS
            )

    else:
        text = "WTF?"
        telegram_bot.send_message(
            chat_id=user_telegram_id,
            text=text,
            reply_markup=main_menu_keyboard
        )


@telegram_bot.callback_query_handler(func=lambda call: True)
def callback_query_handler(callback):
    global telegram_bot

    write_log("CALLBACK" +
              " " +
              str(callback.message.chat.id) +
              " " +
              str(callback.from_user.id) +
              " " +
              str(callback.from_user.username) +
              " " +
              str(callback.data))

    username = callback.from_user.username
    user_telegram_id = callback.from_user.id
    message_id = callback.message.json["message_id"]

    if username is None:
        username = ""
    try:
        user = execute_sql(
            f"SELECT * "
            f"FROM users "
            f"WHERE telegram_id={user_telegram_id}",
            POSTGRES_CONNECTION_PARAMS
        )[0]
        if not user:
            raise IndexError
    except IndexError:
        execute_sql(
            f"INSERT into users(telegram_id, username, current_state_info) "
            f"VALUES ({user_telegram_id}, {adapt(username)}, {Json(current_state_info_default)})",
            POSTGRES_CONNECTION_PARAMS
        )
        user = execute_sql(
            f"SELECT * "
            f"FROM users "
            f"WHERE telegram_id={user_telegram_id}",
            POSTGRES_CONNECTION_PARAMS
        )[0]

    # TODO: add in db last usage
    user_current_state_info = user["current_state_info"]
    callback_type = callback.data.split("|")[0]

    if callback_type == "ad":  # ADmin
        pass
    else:
        telegram_bot.edit_message_text(
            chat_id=user_telegram_id,
            message_id=message_id,
            text="WTF?",
            reply_markup=None
        )


def bot_polling():
    while True:
        try:
            telegram_bot.polling()
        except requests.exceptions.ReadTimeout:
            write_log("READ TIMEOUT ERROR, RECONNECTING")
            exit(0)
        except requests.exceptions.ConnectionError:
            write_log("CONNECTION ERROR, RECONNECTING")
            exit(0)


def main():
    global threads

    write_log("START")

    initialization()
    write_log("INITIALIZATION COMPLETE")

    # schedule_thread = Thread(target=threading_func_schedule_run_pending, daemon=True)
    # schedule_thread.start()
    # threads.append(schedule_thread)
    # write_log("SCHEDULE THREAD STARTED")

    bot_polling_thread = Thread(target=bot_polling)
    bot_polling_thread.start()
    threads.append(bot_polling_thread)
    write_log("BOT_POLLING THREAD STARTED")


if __name__ == '__main__':
    main()
