import telebot
from telebot import types
import time
from pytz import utc
from functools import partial
from apscheduler.schedulers.background import BackgroundScheduler
import sqlite3
from datetime import datetime
from apscheduler.triggers.date import DateTrigger



scheduler = BackgroundScheduler()
scheduler.start

conn = sqlite3.connect('reminders.db', check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS reminders
             (user_id text, event_name text, event_time text, reminded int)''')
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
    bot.register_next_step_handler(message, buttons_click_handler)


    

# Add buttons to the reply keyboard
    

# Send a message with the reply keyboard
 
def buttons_click_handler(message):
    buttonMessages = {
        'Create new task': create_command_handler,
        'Check existing tasks': check_command_handler,
        'Check tasks for week': week_command_handler
    }
    if(message.text in buttonMessages):
        func = buttonMessages[message.text]
        func(message) 
    

def help_command_handler(message):
    text = '<b>/start </b> - starts the bot \n <b>/help </b> - outputs commands \n <b>/createTask </b> - adds your task to database'
    bot.send_message(message.chat.id, text,parse_mode='html')

def create_command_handler(message):
    
    msg = bot.send_message(message.chat.id, 'Please enter the name of action, you want to plan.')
    bot.register_next_step_handler(msg, get_event_name)

def get_event_name(message):
     msg = bot.reply_to(message, f'The name of event is: {message.text}\n Now please enter date in format: DD.MM.YYYY')
     name = message.text
     bot.register_next_step_handler(msg, partial(get_event_date, name=name))
     
     

def get_event_date(message, name):
    if(date_validator(message.text) == True):
        msg = bot.reply_to(message, f'The date of event is: {message.text}\n Now please enter the time in format: HH:MM')
        bot.register_next_step_handler(msg, partial(get_event_time, name= name, date= message.text))
    else:
        msg = bot.reply_to(message, f'The date is invalid! Please try again. the format should be DD.MM.YYYY')
        bot.register_next_step_handler(msg, partial(get_event_date, name=name))
   

def get_event_time(message, name, date):
    if(time_validator(message.text) == True):
        time = message.text
        msg = bot.reply_to(message, f'The time of event is: {time}\n The event is written! {name, date, time}')
        dateAndTime = date+' '+time
        print(dateAndTime)
        add_reminder(message.chat.id, name,dateAndTime)
    else:
        msg = bot.reply_to(message, f'The time is invalid! Try again. The time format should be HH:MM')
        bot.register_next_step_handler(msg, partial(get_event_date, name= name, date= date))

    print(name, date, message.text)




def check_command_handler(message):
    
    print('check')
    

  

def week_command_handler(message):
    
    print('week')


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

def send_reminder(user_id, event_name):
    # Send the reminder to the user
    bot.send_message(user_id, event_name)
    # Update the database to mark the reminder as sent
    c.execute("UPDATE reminders SET reminded = 1 WHERE user_id = ? AND event_name = ?", (user_id, event_name))
    conn.commit()

def schedule_reminder(user_id, event_name, event_time):
    # Convert event_time to a datetime object
    date_format = "%d.%m.%Y %H:%M"
    
    # Convert the string to a datetime object
    datetime_obj = datetime.strptime(event_time, date_format)
    timeOfEvent = datetime_obj.isoformat()
    print(timeOfEvent)
    # Schedule the reminder
    scheduler.add_job(send_reminder, DateTrigger(run_date=timeOfEvent), args=[user_id, event_name], id=f"{user_id}_{event_time}")

def check_for_new_reminders():
    c.execute("SELECT user_id, event_name, event_time FROM reminders WHERE reminded = 0")
    for row in c.fetchall():
        user_id, event_name, event_time = row
        schedule_reminder(user_id, event_name, event_time)

def add_reminder(user_id, event_name, event_time):
    print(user_id, event_name,event_time)
    c.execute("INSERT INTO reminders VALUES (?, ?, ?,?)", (user_id, event_name, event_time, 0))
    conn.commit()
    check_for_new_reminders

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
    }  

    if(command in commands):
         func = commands[command]
         func(message)
    
@bot.callback_query_handler(func=lambda callback: True)
def callback_query(callback):
    
    calls = {
        'create': create_command_handler,
        'check': check_command_handler,
        'week': week_command_handler
    }
    
    if(callback.data in calls):
        func = calls[callback.data]
        func(callback.message)
    
        



bot.polling(non_stop=True)

