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
scheduler.start

conn = mysql.connector.connect(
    host="reminders1.c1c8m6ekuail.us-east-1.rds.amazonaws.com",
    user="admin",
    password="88888888",
    database="reminders",
)
cursor = conn.cursor()

cursor.execute("CREATE TABLE IF NOT EXISTS reminders (id INT AUTO_INCREMENT PRIMARY KEY, user_id text, event_name text, event_time text, reminded int)")
conn.commit()

scheduler = BackgroundScheduler()
scheduler.configure(timezone = utc)

token = '6931846117:AAGL7b10Uk-Gxz13o-RZqSbxQDIevyMwV7U'
bot = telebot.TeleBot(token)





def start_command_handler(message):
    menu = types.BotCommandScope()
    start = types.BotCommand('/start', 'Start the bot!')
    reply_keyboard = types.ReplyKeyboardMarkup()

    createEvent = types.KeyboardButton('Create new task')
    checkEvent = types.KeyboardButton('Check existing tasks')
    checkWeek = types.KeyboardButton('Check tasks for week')
    
    reply_keyboard.add(createEvent)
    reply_keyboard.add(checkEvent)
    reply_keyboard.add(checkWeek)
    
    bot.send_message(message.chat.id, f'Hi! You can choose an option', reply_markup=reply_keyboard)


    

# Add buttons to the reply keyboard
    

# Send a message with the reply keyboard
 

def help_command_handler(message):
    text = '<b>/start </b> - starts the bot \n <b>/help </b> - outputs commands \n <b>/createTask </b> - adds your task to database'
    bot.send_message(message.chat.id, text,parse_mode='html')

def create_command_handler(message):
    # Add Cancel button
    cancel_button = types.InlineKeyboardButton(text='Cancel', callback_data='cancel')
    markup = types.InlineKeyboardMarkup()
    markup.add(cancel_button)

    msg = bot.send_message(message.chat.id, 'Please enter the name of the action you want to plan.', reply_markup=markup)
   
    bot.register_next_step_handler(msg, get_event_name)

def get_event_name(message):
    if (message.text=='/cancel'):
        msg = bot.reply_to(message, f'Action is canceled', reply_markup=markup)
        return
    cancel_button = types.InlineKeyboardButton(text='Cancel', callback_data='cancel')
    markup = types.InlineKeyboardMarkup()
    markup.add(cancel_button)
    
    msg = bot.reply_to(message, f'The name of the event is: {message.text}\nNow please enter the date in the format: DD.MM.YYYY', reply_markup=markup)
    name = message.text
    bot.register_next_step_handler(msg, partial(get_event_date, name=name))

def get_event_date(message, name):
    if (message.text=='/cancel'):
        msg = bot.reply_to(message, f'Action is canceled', reply_markup=markup)
        return
    if date_validator(message.text):
        # Add Cancel button
        cancel_button = types.InlineKeyboardButton(text='Cancel', callback_data='cancel')
        markup = types.InlineKeyboardMarkup()
        markup.add(cancel_button)
        
        msg = bot.reply_to(message, f'The date of the event is: {message.text}\nNow please enter the time in the format: HH:MM', reply_markup=markup)
        bot.register_next_step_handler(msg, partial(get_event_time, name=name, date=message.text))
    else:
        # Add Cancel button
        cancel_button = types.InlineKeyboardButton(text='Cancel', callback_data='cancel')
        markup = types.InlineKeyboardMarkup()
        markup.add(cancel_button)
        
        msg = bot.reply_to(message, f'The date is invalid! Please try again. The format should be DD.MM.YYYY', reply_markup=markup)
        bot.register_next_step_handler(msg, partial(get_event_date, name=name))
   
def get_event_time(message, name, date):
    if (message.text=='/cancel'):
        msg = bot.reply_to(message, f'Action is canceled', reply_markup=markup)
        return
    if time_validator(message.text):
        time = message.text
        msg = bot.reply_to(message, f'The time of the event is: {time}\nThe event is written! {name, date, time}')
        date_and_time = date + ' ' + time
        print(date_and_time)
        add_reminder(message.chat.id, name, date_and_time)
    else:
        # Add Cancel button
        cancel_button = types.InlineKeyboardButton(text='Cancel', callback_data='cancel')
        markup = types.InlineKeyboardMarkup()
        markup.add(cancel_button)
        
        msg = bot.reply_to(message, f'The time is invalid! Try again. The time format should be HH:MM', reply_markup=markup)
        bot.register_next_step_handler(msg, partial(get_event_time, name=name, date=date))






def date_validator(date_text):
    date = date_text
    if(len(date) != 10):
        return False
    numbersFromDate = date[0:2]+date[3:5] + date[6:10]
    try:
        int(numbersFromDate)
    except:
        return False
    dotsFromDate = date[2]+date[5]
    if(dotsFromDate != '..'):
        return False
    return True

def time_validator(time_text):
    time = time_text
    if(len(time) != 5):
        return False
    numbersFromDate = time[0:2]+time[3:5]
    try:
        int(numbersFromDate)
    except:
        return False
    if(time[2] != ':'):
        return False
    return True

def delete_expired_reminders():
    current_time = datetime.utcnow()
    cursor.execute("DELETE FROM reminders WHERE event_time <= %s OR reminded = 1", (current_time,))
    conn.commit()

def send_reminder(user_id, event_name):
    # Send the reminder to the user
    bot.send_message(user_id, event_name)
    # Update the database to mark the reminder as sent
    cursor.execute("UPDATE reminders SET reminded = 1 WHERE user_id = %s AND event_name = %s", (user_id, event_name))
    conn.commit()
    delete_expired_reminders()
    check_for_new_reminders()


def schedule_reminder(user_id, event_name, event_time):
    # Convert event_time to a datetime object
    date_format = "%d.%m.%Y %H:%M"
    
    # Convert the string to a datetime object
    datetime_obj = datetime.strptime(event_time, date_format)
    timeOfEvent = datetime_obj.isoformat()
    
    # Generate a UUID for the job ID
    job_id = str(uuid.uuid4())
    
    # Schedule the reminder
    scheduler.add_job(send_reminder, DateTrigger(run_date=timeOfEvent), args=[user_id, event_name], id=job_id)

def check_for_new_reminders():
    cursor.execute("SELECT user_id, event_name, event_time FROM reminders WHERE reminded = 0")
    for row in cursor.fetchall():
        user_id, event_name, event_time = row
        schedule_reminder(user_id, event_name, event_time)

def add_reminder(user_id, event_name, event_time):
    print(user_id, event_name,event_time)
    cursor.execute("INSERT INTO reminders (user_id, event_name, event_time, reminded) VALUES (%s, %s, %s, %s)", (user_id, event_name, event_time, 0))
    conn.commit()
    schedule_reminder(user_id, event_name, event_time)

def check_command_handler(message):
    # Get user_id from the message
    user_id = message.chat.id
    
    # Retrieve tasks for the user from the database
    cursor.execute("SELECT event_name, event_time FROM reminders WHERE user_id = %s", (user_id,))
    tasks = cursor.fetchall()
    
    # Format tasks as a list of strings
    task_list = []
    for task in tasks:
        event_name, event_time = task
        task_list.append(f"{event_name}, {event_time}")
    
    # If there are tasks, send them to the user
    if task_list:
        task_text = "\n".join(task_list)
        bot.send_message(user_id, f"Your existing tasks:\n{task_text}")
    else:
        bot.send_message(user_id, "You have no existing tasks.") 

def check_day_handler(message):
    user_id = message.chat.id
    
    # Get today's date
    today_date = datetime.utcnow().date()
    
    # Retrieve tasks for today for the user from the database
    cursor.execute("SELECT event_name, event_time FROM reminders WHERE user_id = %s AND DATE(event_time) = %s", (user_id, today_date))
    tasks = cursor.fetchall()
    
    # Format tasks for today as a list of strings
    task_list = []
    for task in tasks:
        event_name, event_time = task
        task_list.append(f"{event_name}, {event_time.strftime('%H:%M')}")
    
    # If there are tasks for today, send them to the user
    if task_list:
        task_text = "\n".join(task_list)
        bot.send_message(user_id, f"Your tasks for today:\n{task_text}")
    else:
        bot.send_message(user_id, "You have no tasks for today.")

def convert_date_format(date_str):
    # Split the original date string by the dot separator
    day, month, year = date_str.split('.')
    
    # Reformat the date string to 'yyyy.mm.dd'
    new_date_str = f"{year}-{month}-{day}"
    
    return new_date_str

scheduler.start()

@bot.message_handler()
def command_parse(message):
    command = message.text
    commands = {
        '/start': start_command_handler,
        '/help': help_command_handler,
        'Create new task': create_command_handler,
        'Check existing tasks': check_command_handler,
        'Check tasks for today': check_day_handler     
    }  

    if(command in commands):
         func = commands[command]
         func(message)
    
@bot.callback_query_handler(func=lambda call: call.data == 'cancel')
def cancel_action(call):
    bot.send_message(call.message.chat.id, 'Action is canceled.')
    bot.clear_step_handler_by_chat_id(chat_id=call.message.chat.id)
    


bot.polling(non_stop=True)

