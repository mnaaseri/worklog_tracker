from aiogram.types import (InlineKeyboardButton, InlineKeyboardMarkup,
                           ReplyKeyboardMarkup)


yes_no_reply_keyboard= ReplyKeyboardMarkup( 
    resize_keyboard=True, one_time_keyboard=True).add("Yes", "No")


today_worklog_reply_keyboard= ReplyKeyboardMarkup( 
    resize_keyboard=True, one_time_keyboard=True).add("Today", "Other Day")


worklog_status_keyboard_reply = ReplyKeyboardMarkup( 
    resize_keyboard=True, one_time_keyboard=True).add("started", "ended")