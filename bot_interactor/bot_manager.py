import json
from datetime import datetime
from dotenv import load_dotenv
import os
import requests
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import (InlineKeyboardButton, InlineKeyboardMarkup,
                           ReplyKeyboardMarkup)
from aiogram.dispatcher import FSMContext
from aiogram.contrib.fsm_storage.memory import MemoryStorage 

from persiantools.jdatetime import JalaliDate
from input_states import (LeaveInputState, WorkLogInputState,
                          LeaveDayForm, SingupStates)
from reply_keyboards import (yes_no_reply_keyboard, today_worklog_reply_keyboard,
                             worklog_status_keyboard_reply)

from helper_utils import format_leave_response, format_worklog_response

load_dotenv()

BASE_API_URL = os.getenv('BASE_API_URL')

TELEGRAM_API_TOKEN = os.getenv('TELEGRAM_API_TOKEN')


storage = MemoryStorage()
bot = Bot(token=TELEGRAM_API_TOKEN, parse_mode='HTML')
dp = Dispatcher(bot, storage=storage)


# Define the main menu inline keyboard
main_menu_keyboard = InlineKeyboardMarkup(row_width=2)
main_menu_keyboard.add(
    InlineKeyboardButton(text="Sing Up", callback_data="sign_up"),
    InlineKeyboardButton(text="Add Worklog", callback_data="add_worklog"),
    InlineKeyboardButton(text="Add Leave Day", callback_data="add_leaveday"),
    InlineKeyboardButton(text="Get Worklogs", callback_data="get_worklog"),
    InlineKeyboardButton(text="Get Leave Days", callback_data="get_leaveday")
)


@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    await message.reply("Main Menu", reply_markup=main_menu_keyboard)


@dp.callback_query_handler(text=["add_worklog", "add_leaveday", "get_worklog", "get_leaveday", "sign_up"])
async def check_button(call: types.CallbackQuery):

    if call.data == "add_worklog":
        await call.message.answer("Do you want to log today's work log?",
                                  reply_markup=today_worklog_reply_keyboard)
        await WorkLogInputState.confirm_today.set()
        
    elif call.data == "add_leaveday":
        await call.message.answer("Do you want to add a leave day for today?",
                                  reply_markup=yes_no_reply_keyboard)
        
    elif call.data == "get_worklog":
        await call.message.answer("Please enter the Jalali year and month for the work logs (e.g., 1402 7 for Mehr 1402).")
        await LeaveInputState.get_worklog.set()

    elif call.data == "get_leaveday":
        await call.message.answer("Please enter the Jalali year and month for the leave days (e.g., 1402 7 for Mehr 1402).")
        await LeaveInputState.get_leave.set()
        
    elif call.data == "sign_up":
        await call.message.answer("Please enter a username")
        await SingupStates.username.set()
    
    await call.answer()


@dp.message_handler(state=SingupStates.username)
async def handle_get_email(message: types.Message, state: FSMContext):
    await state.update_data(username=message.text)
    await message.reply("Please Enter Your Email")
    await SingupStates.next()

@dp.message_handler(state=SingupStates.email)
async def handle_get_password(message: types.Message, state: FSMContext):
    await state.update_data(email=message.text)
    await message.reply("Please Enter Your Password")
    await SingupStates.next()

@dp.message_handler(state=SingupStates.password)
async def handle_repeat_password(message: types.Message, state: FSMContext):
    await state.update_data(password=message.text)
    await message.reply("Please Repeat Your Password")
    await SingupStates.next()
    
@dp.message_handler(state=SingupStates.password2)
async def call_sign_up_api(message: types.Message, state: FSMContext):
    await state.update_data(password2=message.text)
    
    data = await state.get_data()
    username = data['username']
    email = data["email"]
    password = data['password']
    password2 = data['password2']
    telegram_id = message.from_user.id

    api_data = {
        "username": username,
        "email": email,
        "telegram_id": telegram_id,
        "password": password,
        "password2": password2
    }

    response = requests.post(
        f"{BASE_API_URL}/user-signup/",
        headers={'Content-Type': 'application/json'},
        json=api_data, timeout=10
    )

    if response.status_code == 201:
        await message.reply("Account Created Successfuly!")
        await message.answer("What would you like to do next?", reply_markup=main_menu_keyboard)
    else:
        await message.reply(f"Failed to add work log. Error: {response.text}")
        await message.answer("What would you like to do next?", reply_markup=main_menu_keyboard)

    await state.finish() 


@dp.message_handler(lambda message: message.text in ["Today", "Other Day"], state=WorkLogInputState.confirm_today)
async def handle_today_confirmation(message: types.Message, state: FSMContext):
    if message.text == "Today":
        await message.answer("Are you starting or finishing your work?", reply_markup=worklog_status_keyboard_reply)
        await state.finish()
    else:
        await message.answer("Please enter the date for the work log in the format YYYY-MM-DD (e.g., 1403-07-10).")
        await WorkLogInputState.input_date.set()


@dp.message_handler(state=WorkLogInputState.input_date)
async def handle_custom_date(message: types.Message, state: FSMContext):
    custom_date = message.text
    try:
        datetime.strptime(custom_date, "%Y-%m-%d")
        await state.update_data(custom_date=custom_date)
        await message.answer("Please enter the time for the work log in the format HH:MM (e.g., 09:00).")
        await WorkLogInputState.input_time.set() 
    except ValueError:
        await message.answer("Invalid date format. Please enter in YYYY-MM-DD format (e.g., 1403-07-10).")


@dp.message_handler(state=WorkLogInputState.input_time)
async def handle_custom_time(message: types.Message, state: FSMContext):
    custom_time = message.text
    try:
        datetime.strptime(custom_time, "%H:%M")
        data = await state.get_data()
        custom_date = data.get("custom_date")
        custom_datetime = f"{custom_date}T{custom_time}:00"
        
        await state.update_data(custom_datetime=custom_datetime)
        await message.answer("Are you starting or finishing your work?", reply_markup=worklog_status_keyboard_reply)
        await WorkLogInputState.call_api.set()

    except ValueError:
        await message.answer("Invalid time format. Please enter in HH:MM format.")


@dp.message_handler(lambda message: message.text in ["started", "ended"], state=WorkLogInputState.call_api)
async def handle_worklog_status(message: types.Message, state: FSMContext):
    telegram_id = message.from_user.id
    worklog_status = message.text

    data = await state.get_data()
    custom_datetime = data.get("custom_datetime", None)

    if custom_datetime:
        try:
            jalali_date_str, time_str = custom_datetime.split('T')
            jalali_year, jalali_month, jalali_day = map(int, jalali_date_str.split('-'))

            jalali_date = JalaliDate(jalali_year, jalali_month, jalali_day)
            gregorian_date = jalali_date.to_gregorian()

            recorded_time = f"{gregorian_date}T{time_str}"
        except ValueError:
            await message.reply(f"Invalid custom datetime format: {custom_datetime}. Please try again.")
            return
    else:
        recorded_time = datetime.now().isoformat()

    data = {
        "status": worklog_status,
        "comment": "",
        "recorded_time": recorded_time
    }

    response = requests.post(
        f"{BASE_API_URL}/worklog/add/{telegram_id}/",
        headers={'Content-Type': 'application/json'},
        json=data,
        timeout=10
    )

    if response.status_code == 201:
        await message.reply("Work log successfully added!", reply_markup=main_menu_keyboard)
    else:
        await message.reply(f"Failed to add work log. Error: {response.text}")

    await message.answer("What would you like to do next?", reply_markup=main_menu_keyboard)


@dp.message_handler(state=LeaveInputState.get_worklog)
async def get_worklog_jalali(message: types.Message, state: FSMContext):
    telegram_id = message.from_user.id
    try:
        jalali_year, jalali_month = map(int, message.text.split())
        
        response = requests.get(f"{BASE_API_URL}/worklog/jalali/monthly/{telegram_id}/{jalali_year}/{jalali_month}/")
        if response.status_code == 200:
            worklog_data = response.json()
            await message.answer(format_worklog_response(worklog_data))
        else:
            await message.answer(f"Unable to fetch work logs at the moment. {response.text}")
    except ValueError:
        await message.answer("Invalid format. Please enter the Jalali year and month as two numbers (e.g., 1402 7).")
    finally:
        await state.finish()
        
        await message.answer("What would you like to do next?", reply_markup=main_menu_keyboard)


@dp.message_handler(state=LeaveInputState.get_leave)
async def get_leave_jalali(message: types.Message, state: FSMContext):
    telegram_id = message.from_user.id
    try:
        jalali_year, jalali_month = map(int, message.text.split())
        
        response = requests.get(f"{BASE_API_URL}/leave/jalali/monthly/{telegram_id}/{jalali_year}/{jalali_month}/")
        if response.status_code == 200:
            leave_data = response.json()
            await message.answer(format_leave_response(leave_data))
        else:
            await message.answer(f"Unable to fetch leave records at the moment. {response.text}", reply_markup=main_menu_keyboard)
    except ValueError:
        await message.answer("Invalid format. Please enter the Jalali year and month as two numbers (e.g., 1402 7).")
    finally:
        await state.finish()
        await message.answer("What would you like to do next?", reply_markup=main_menu_keyboard)


@dp.message_handler(lambda message: message.text in ["Yes", "No"])
async def handle_leave_day(message: types.Message, state: FSMContext):
    if message.text == "Yes":
        telegram_id = message.from_user.id
        current_date = datetime.now().date().isoformat()

        data = {
            "leave_date": current_date,
            "reason": "User-initiated leave day",
        }

        response = requests.post(
            f"{BASE_API_URL}/leave/add/{telegram_id}/",
            headers={'Content-Type': 'application/json'},
            json=data, timeout=10
        )

        if response.status_code == 201:
            await message.reply("Leave day successfully added!")
        else:
            await message.reply("Failed to add leave day. Please try again.", [response.text])
            await message.answer("What would you like to do next?", reply_markup=main_menu_keyboard)

    else:
        await message.reply("Please provide the leave date in the format YYYY-MM-DD:")
        await LeaveDayForm.leave_date.set()
        


@dp.message_handler(state=LeaveDayForm.leave_date)
async def process_leave_date(message: types.Message, state: FSMContext):
    await state.update_data(leave_date=message.text)
    await message.reply("Now, please provide the start time in the format HH:MM:")
    await LeaveDayForm.next()


@dp.message_handler(state=LeaveDayForm.start_time)
async def process_start_time(message: types.Message, state: FSMContext):
    await state.update_data(start_time=message.text)
    await message.reply("Finally, provide the end time in the format HH:MM:")
    await LeaveDayForm.next()
    

@dp.message_handler(state=LeaveDayForm.end_time)
async def process_end_time(message: types.Message, state: FSMContext):
    data = await state.get_data()
    leave_date = data['leave_date']
    start_time = data['start_time']
    end_time = message.text
    telegram_id = message.from_user.id

    api_data = {
        "jalali_leave_date": leave_date,
        "start_time": start_time,
        "end_time": end_time
    }

    response = requests.post(
        f"{BASE_API_URL}/leave/add/{telegram_id}/",
        headers={'Content-Type': 'application/json'},
        json=api_data, timeout=10
    )

    if response.status_code == 201:
        await message.reply("Leave day successfully added with custom times!")
        await message.answer("What would you like to do next?", reply_markup=main_menu_keyboard)
    else:
        await message.reply(f"Failed to add leave day. Please try again.{response.text}")
        await message.answer("What would you like to do next?", reply_markup=main_menu_keyboard)

    await state.finish() 

executor.start_polling(dp)

