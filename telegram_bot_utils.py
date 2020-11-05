# -*- coding: utf-8 -*-

import datetime
import psycopg2
from psycopg2.extras import RealDictCursor
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

from moviepy.editor import *
from contextlib import closing


def execute_sql(sql_query, connection_params):
    with closing(psycopg2.connect(cursor_factory=RealDictCursor,
                                  dbname=connection_params["dbname"],
                                  user=connection_params["user"],
                                  password=connection_params["password"],
                                  host=connection_params["host"],
                                  port=connection_params["port"],
                                  )) as conn:
        conn.autocommit = True
        with conn.cursor() as cursor:
            cursor.execute(sql_query)
            try:
                records = cursor.fetchall()
                result = []
                for record in records:
                    result.append(dict(record))
                return result
            except psycopg2.ProgrammingError:
                pass


def gen_markup(buttons_with_callback):
    # buttons_with_callback_example = [
    #     {
    #         "text": "Bullet in my head",
    #         "callback_data": "42|0"
    #     },
    #     {
    #         "text": "Finally",
    #         "callback_data": "42|21"
    #     }
    # ]

    markup = InlineKeyboardMarkup()
    buttons_with_callback_len = len(buttons_with_callback)
    # markup.row_width = buttons_with_callback_len

    for i in range(buttons_with_callback_len):
        markup.add(InlineKeyboardButton(text=buttons_with_callback[i]["text"],
                                        callback_data=buttons_with_callback[i]["callback_data"]))

    return markup


def write_log(log):
    log = str(datetime.datetime.now()) + " " + log + "\n"
    print(log, end="")
    with open("logs.txt", "a") as f:
        f.write(log)


def send_text(bot, telegram_id, text_id, pg_connection_params):
    text = execute_sql(f"SELECT text "
                       f"FROM texts "
                       f"WHERE id={text_id}",
                       pg_connection_params)[0]["text"]
    bot.send_message(telegram_id, text=text, reply_markup=None, parse_mode="HTML")


def send_photo(bot, telegram_id, photo_id, caption, pg_connection_params):
    photo = execute_sql(f"SELECT raw "
                        f"FROM photos "
                        f"WHERE id={photo_id}",
                        pg_connection_params)[0]["raw"]
    bot.send_photo(telegram_id, photo=photo, caption=caption)


def send_video(bot, telegram_id, video_id, caption, pg_connection_params):
    video = execute_sql(f"SELECT raw "
                        f"FROM videos "
                        f"WHERE id={video_id}",
                        pg_connection_params)[0]["raw"]
    bot.send_video(telegram_id, data=video, caption=caption)


def send_video_note(bot, telegram_id, video_note_id, pg_connection_params):
    video_note = execute_sql(f"SELECT raw "
                             f"FROM video_notes "
                             f"WHERE id={video_note_id}",
                             pg_connection_params)[0]["raw"]
    bot.send_video_note(telegram_id, data=video_note)


def crop_video_to_square(video_bytes):
    with open("in", "wb") as f:
        f.write(video_bytes)

    clip = VideoFileClip("in")
    width = clip.w
    height = clip.h

    if height < width:
        x1 = (width - height) / 2
        x2 = (width - height) / 2 + height
        new_clip = clip.fx(vfx.crop, x1=x1, x2=x2)
    else:
        y1 = (height - width) / 2
        y2 = (height - width) / 2 + width
        new_clip = clip.fx(vfx.crop, y1=y1, y2=y2)
    new_clip.write_videofile("out.mp4")

    with open("out.mp4", "rb") as f:
        video_bytes = f.read()

    os.remove("in")
    os.remove("out.mp4")

    return video_bytes
