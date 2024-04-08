import telebot
from telebot import types

import time



token = '6931846117:AAGL7b10Uk-Gxz13o-RZqSbxQDIevyMwV7U'
bot = telebot.TeleBot(token)




def start_command_handler(message):
    
    reply_keyboard = types.ReplyKeyboardMarkup()

# Add buttons to the reply keyboard
    createEvent = types.KeyboardButton('Create new task')
    checkEvent = types.KeyboardButton('Check existing tasks')
    checkWeek = types.KeyboardButton('Check tasks for week')
    
    reply_keyboard.add(createEvent)
    reply_keyboard.add(checkEvent)
    reply_keyboard.add(checkWeek)
    bot.send_message(message.chat.id, f'Hi! You can choose an option', reply_markup=reply_keyboard)
    bot.register_next_step_handler(message, buttons_click_handler)

    

# Send a message with the reply keyboard
 
def buttons_click_handler(message):
    buttonMessages = {
        'Create new task': create_command_handler,
        'Check existing tasks': check_command_handler,
        'Check tasks for week': week_command_handler
    }
    print(message.text)
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
     bot.register_next_step_handler(msg, get_event_date)

def get_event_date(message):
    msg = bot.reply_to(message, f'The date of event is: {message.text}\n Now please enter the time in format: HH:MM')
    bot.register_next_step_handler(msg, get_event_time)

def get_event_time(message):
    bot.reply_to(message, f'The the of event is: {message.text}\n The event is written!')



def check_command_handler(message):
    
    print('check')
    

  

def week_command_handler(message):
    
    print('week')


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
