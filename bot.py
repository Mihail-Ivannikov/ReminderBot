import telebot
from telebot import types
import time
from pytz import utc
from functools import partial
from apscheduler.schedulers.background import BackgroundScheduler
import mysql.connector
from datetime import datetime
from apscheduler.triggers.date import DateTrigger
import uuid


scheduler = BackgroundScheduler()
scheduler.configure(timezone = utc)
scheduler.start()

conn = mysql.connector.connect(
    host="reminders1.c1c8m6ekuail.us-east-1.rds.amazonaws.com",
    user="admin",
    password="88888888",
    database="reminders",
)

cursor = conn.cursor()

cursor.execute("CREATE TABLE IF NOT EXISTS reminders (id INT AUTO_INCREMENT PRIMARY KEY, user_id text, event_name text, event_time text, reminded int)")
conn.commit()

token = '6931846117:AAGL7b10Uk-Gxz13o-RZqSbxQDIevyMwV7U'
bot = telebot.TeleBot(token)

def start_command_handler(message):
    reply_keyboard = types.ReplyKeyboardMarkup()
    createEvent = types.KeyboardButton('Create new task')
    checkEvent = types.KeyboardButton('Check existing tasks')
    checkDay = types.KeyboardButton('Check tasks for today')
    reply_keyboard.add(createEvent)
    reply_keyboard.add(checkEvent)
    reply_keyboard.add(checkDay)
    bot.send_message(message.chat.id, f'Hi! You can choose an option', reply_markup=reply_keyboard)


def help_command_handler(message):
    text = '<b>/start </b> - starts the bot \n <b>/help </b> - outputs commands \n <b>/createTask </b> - adds your task to database'
    bot.send_message(message.chat.id, text,parse_mode='html')

def create_reminder_handler(message):
    cancel_button = types.InlineKeyboardButton(text='Cancel', callback_data='cancel')
    markup = types.InlineKeyboardMarkup()
    markup.add(cancel_button)
    msg = bot.send_message(message.chat.id, 'Please enter the name of the action you want to plan.', reply_markup=markup)
    bot.register_next_step_handler(msg, get_event_name)


def get_event_name(message):
    cancel_button = types.InlineKeyboardButton(text='Cancel', callback_data='cancel')
    markup = types.InlineKeyboardMarkup()
    markup.add(cancel_button)
    msg = bot.reply_to(message, f'The name of the event is: {message.text}\nNow please enter the date in the format: DD.MM.YYYY', reply_markup=markup)
    name = message.text
    bot.register_next_step_handler(msg, partial(get_event_date, name=name))

def get_event_date(message, name):
    if is_date_valid(message.text):
        cancel_button = types.InlineKeyboardButton(text='Cancel', callback_data='cancel')
        markup = types.InlineKeyboardMarkup()
        markup.add(cancel_button)
        msg = bot.reply_to(message, f'The date of the event is: {message.text}\nNow please enter the time in the format: HH:MM', reply_markup=markup)
        bot.register_next_step_handler(msg, partial(get_event_time, name=name, date=message.text))
    else:
        cancel_button = types.InlineKeyboardButton(text='Cancel', callback_data='cancel')
        markup = types.InlineKeyboardMarkup()
        markup.add(cancel_button)
        msg = bot.reply_to(message, f'The date is invalid! Please try again. The format should be DD.MM.YYYY', reply_markup=markup)
        bot.register_next_step_handler(msg, partial(get_event_date, name=name))
   
def get_event_time(message, name, date):
    if is_time_valid(message.text):
        time = message.text
        msg = bot.reply_to(message, f'The time of the event is: {time}\nThe event is written! {name, date, time}')
        date_and_time = date + ' ' + time
        print(date_and_time)
        add_reminder(message.chat.id, name, date_and_time)
    else:
        cancel_button = types.InlineKeyboardButton(text='Cancel', callback_data='cancel')
        markup = types.InlineKeyboardMarkup()
        markup.add(cancel_button)
        msg = bot.reply_to(message, f'The time is invalid! Try again. The time format should be HH:MM', reply_markup=markup)
        bot.register_next_step_handler(msg, partial(get_event_time, name=name, date=date))


def is_date_valid(date_text):
    try:
        datetime.strptime(date_text, '%d.%m.%Y')
        return True
    except ValueError:
        return False

def is_time_valid(time_text):
    try:
        datetime.strptime(time_text, '%H:%M')
        return True
    except ValueError:
        return False

def delete_expired_reminders():
    current_time = datetime.utcnow()
    cursor.execute("DELETE FROM reminders WHERE event_time <= %s OR reminded = 1", (current_time,))
    conn.commit()

def send_reminder_message(user_id, event_name):
    bot.send_message(user_id, "❗❗❗"+event_name+"❗❗❗")
    cursor.execute("UPDATE reminders SET reminded = 1 WHERE user_id = %s AND event_name = %s", (user_id, event_name))
    conn.commit()
    delete_expired_reminders()
    check_for_new_reminders()


def add_reminder_scheduler(user_id, event_name, event_time):
    date_format = "%d.%m.%Y %H:%M"
    datetime_obj = datetime.strptime(event_time, date_format)
    timeOfEvent = datetime_obj.isoformat()
    job_id = str(uuid.uuid4())
    scheduler.add_job(send_reminder_message, DateTrigger(run_date=timeOfEvent), args=[user_id, event_name], id=job_id)

def check_for_new_reminders():
    cursor.execute("SELECT user_id, event_name, event_time FROM reminders WHERE reminded = 0")
    for row in cursor.fetchall():
        user_id, event_name, event_time = row
        add_reminder_scheduler(user_id, event_name, event_time)

def add_reminder(user_id, event_name, event_time):
    print(user_id, event_name,event_time)
    cursor.execute("INSERT INTO reminders (user_id, event_name, event_time, reminded) VALUES (%s, %s, %s, %s)", (user_id, event_name, event_time, 0))
    conn.commit()
    add_reminder_scheduler(user_id, event_name, event_time)

def check_existing_reminders_handler(message):
    user_id = message.chat.id
    cursor.execute("SELECT event_name, event_time FROM reminders WHERE user_id = %s", (user_id,))
    tasks = cursor.fetchall()
    task_list = []
    for task in tasks:
        event_name, event_time = task
        task_list.append(f"{event_name}, {event_time}")
    if task_list:
        task_text = "\n".join(task_list)
        bot.send_message(user_id, f"Your existing tasks:\n{task_text}")
    else:
        bot.send_message(user_id, "You have no existing tasks.")

def check_today_reminders_handler(message):
    user_id = (message.chat.id,) 
    today_date_obj = datetime.utcnow().date()
    today_date = str(today_date_obj.strftime('%d.%m.%Y'))
    cursor.execute("SELECT event_name, event_time FROM reminders WHERE user_id = %s", user_id)
    tasks = cursor.fetchall()
    task_list = []
    for task in tasks:
        event_name, event_time = task
        if (event_time[:10] == today_date):
            task_list.append(f"{event_name}, {event_time[10:]}")
    if task_list:
        task_text = "\n".join(task_list)
        bot.send_message(user_id[0], f"Your tasks for today:\n{task_text}")  # Accessing the first element of the tuple
    else:
        bot.send_message(user_id[0], "You have no tasks for today.")

def date_format_converter(date_str):
    day, month, year = date_str.split('.')
    new_date_str = f"{year}-{month}-{day}"
    return new_date_str

@bot.message_handler()
def command_parse(message):
    command = message.text
    commands = {
        '/start': start_command_handler,
        '/help': help_command_handler,
        'Create new task': create_reminder_handler,
        'Check existing tasks': check_existing_reminders_handler,
        'Check tasks for today': check_today_reminders_handler     
    }  

    if(command in commands):
         func = commands[command]
         func(message)
    
@bot.callback_query_handler(func=lambda call: call.data == 'cancel')
def cancel_action(call):
    bot.send_message(call.message.chat.id, 'Action is canceled.')
    bot.clear_step_handler_by_chat_id(chat_id=call.message.chat.id)
    


bot.polling(non_stop=True)

