import telebot
import time



token = '6931846117:AAGL7b10Uk-Gxz13o-RZqSbxQDIevyMwV7U'
bot = telebot.TeleBot(token)


def start_command_handler(message):
    bot.send_message(message.chat.id, f'Hi! ${time.ctime()}')
    return 0

def help_command_handler(message):
    text = '<b>/start </b> - starts the bot \n <b>/help </b> - outputs commands \n <b>/createTask </b> - adds your task to database'
    bot.send_message(message.chat.id, text,parse_mode='html')
def create_command_handler(message):
    #remove with code!!!!!!!
    pass

@bot.message_handler()
def command_parse(message):
    command = message.text
    commands = {
        '/start': start_command_handler,
        '/help': help_command_handler,
        '/createTask': create_command_handler,
        
        
    }   

    if(command in commands):
         func = commands[command]
         func(message)
    

bot.polling(non_stop=True)

