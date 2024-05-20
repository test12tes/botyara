import logging
import re
import paramiko
from telegram import Update, ForceReply
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler
import psycopg2
from psycopg2 import Error
from dotenv import load_dotenv
import os
import subprocess

load_dotenv()

TOKEN = os.getenv("TOKEN")
LOG_FILE_PATH = "/var/log/postgresql/postgresql.log"
RM_HOST = os.getenv("RM_HOST")
RM_PORT = os.getenv("RM_PORT")
RM_USER = os.getenv("RM_USER")
RM_PASSWORD = os.getenv("RM_PASSWORD")

DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_DATABASE = os.getenv("DB_DATABASE")
DB_PORT = os.getenv("DB_PORT")

# Подключаем логирование
logging.basicConfig(
    filename='logfile.txt', format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)


def start(update: Update, context):
    user = update.effective_user
    update.message.reply_text(f'Привет {user.full_name}!')


def helpCommand(update: Update, context):
    update.message.reply_text('Доступные команды:\n /find_email\n /find_phone_number\n /verify_password\n /get_release\n /get_uname\n /get_uptime\n /get_df\n /get_free\n /get_mpstat\n /get_w\n /get_auths\n /get_critical\n /get_ps\n /get_ss\n /get_apt_list\n /get_services\n /get_repl_logs\n /get_emails\n /get_phone_numbers\n')


def findPhoneNumbersCommand(update: Update, context):
    update.message.reply_text('Введите текст для поиска телефонных номеров: ')

    return 'findPhoneNumbers'
def findPhoneNumbers (update: Update, context):
    user_input = update.message.text # Получаем текст, содержащий(или нет) номера телефонов

    #phoneNumRegex = re.compile(r'8 \(\d{3}\) \d{3}-\d{2}-\d{2}') # формат 8 (000) 000-00-00
    phoneNumRegex = re.compile(r'\+?[87]{1}[\- ]?\(?\d{3}\)?[\- ]?\d{3}[\- ]?\d{2}[\- ]?\d{2}') # формат 8 (000) 000-00-00
    phoneNumberList = phoneNumRegex.findall(user_input) # Ищем номера телефонов

    if not phoneNumberList: # Обрабатываем случай, когда номеров телефонов нет
        update.message.reply_text('Телефонные номера не найдены')
        return ConversationHandler.END # Завершаем выполнение функции
    phoneNumbers = '' # Создаем строку, в которую будем записывать номера телефонов
    for i in range(len(phoneNumberList)):
        phoneNumbers += f'{i+1}. {phoneNumberList[i]}\n' # Записываем очередной номер
    update.message.reply_text(phoneNumbers) # Отправляем сообщение пользователю
    update.message.reply_text('Хотите добавить в базу данных? Напишите "да" для добавления и "нет" или что угодно для ничего')
    context.user_data['phone_numbers'] = phoneNumberList # передача переменной далее
    return 'findPhoneNumbersSavedb' # Некст хоп оф дайлог

def findPhoneNumbersSavedb (update: Update, context):
    user_input = update.message.text # Получаем текст, содержащий(или нет) номера телефонов
    connection = None

    if user_input=='да':
            try:
                phoneNumberList = context.user_data.get('phone_numbers', [])
                connection = psycopg2.connect(user=DB_USER,
                                  password=DB_PASSWORD,
                                  host=DB_HOST,
                                  port=DB_PORT, 
                                  database=DB_DATABASE)

                cursor = connection.cursor()
                for i in range(len(phoneNumberList)):
                    cursor.execute(f"INSERT INTO Phones (Phone) VALUES ('{phoneNumberList[i]}');")
                connection.commit()
                update.message.reply_text("Sucess")
            except (Exception, Error) as error:
                update.message.reply_text("Error PostgreSQL: {}".format(error))
            finally:
                if connection:
                    cursor.close()
                    connection.close()
                    update.message.reply_text("Connection with PostgreSQL is closed")
    else:
        update.message.reply_text('Не хотите- как хотите. Завершаю работу')
        return ConversationHandler.END # Завершаем выполнение функции

    return ConversationHandler.END # Завершаем работу обработчика диалога

def PasswordCheckCommand(update: Update, context):
    update.message.reply_text('Введите пароль для проверки: ')

    return 'PasswordCheck'
def PasswordCheck (update: Update, context):
    user_input = update.message.text # Получаем текст, содержащий пароль

    
    PasswordRegex = re.compile(r'(?=.*[0-9].*)(?=.*[a-z].*)(?=.*[A-Z].*)(?=.*[!@#$%^&*().].*)^[0-9a-zA-Z!@#$%^&*().]{8,}$') # проверка проля на сложность
    PasswordList = PasswordRegex.search(user_input) # Ищем совпадение с регуляркой

    if not PasswordList: # Пароль простой
        update.message.reply_text('Пароль простой')
        return ConversationHandler.END # Завершаем выполнение функции
    else: # Пароль Сложный
        update.message.reply_text('Пароль сложный') # Отправляем сообщение пользователю
        return ConversationHandler.END # Завершаем работу обработчика диалога
    
        
    

def findEmailCommand(update: Update, context):
    update.message.reply_text('Введите текст для поиска email: ')

    return 'findEmail'
def findEmail (update: Update, context):
    user_input = update.message.text # Получаем текст, содержащий(или нет) емейлы

    
    EmailRegex = re.compile(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+') # Регулярка
    EmailList = EmailRegex.findall(user_input) # Ищем емейлы

    if not EmailList: # Обрабатываем случай, когда емейлов нет
        update.message.reply_text('Емейлов нема')
        return ConversationHandler.END # Завершаем выполнение функции
    
    Email = '' # Создаем строку, в которую будем записывать емейлы
    for i in range(len(EmailList)):
        Email += f'{i+1}. {EmailList[i]}\n' # Записываем очередной емейл
        
    update.message.reply_text(Email) # Отправляем сообщение пользователю
    update.message.reply_text('Хотите добавить в базу данных? Напишите "да" для добавления и "нет" или что угодно для ничего')
    context.user_data['emails'] = EmailList # передача переменной далее
    return 'findEmailsSavedb' # Завершаем работу обработчика диалога

def findEmailsSavedb (update: Update, context):
    user_input = update.message.text # Получаем текст, содержащий(или нет) номера телефонов
    connection = None

    if user_input=='да':
            try:
                EmailList = context.user_data.get('emails', [])
                connection = psycopg2.connect(user=DB_USER,
                                  password=DB_PASSWORD,
                                  host=DB_HOST,
                                  port=DB_PORT, 
                                  database=DB_DATABASE)

                cursor = connection.cursor()
                for i in range(len(EmailList)):
                    cursor.execute(f"INSERT INTO Emails (Email) VALUES ('{EmailList[i]}');")
                connection.commit()
                update.message.reply_text("Sucess")
            except (Exception, Error) as error:
                update.message.reply_text("Error PostgreSQL: {}".format(error))
            finally:
                if connection:
                    cursor.close()
                    connection.close()
                    update.message.reply_text("Connection with PostgreSQL is closed")
    else:
        update.message.reply_text('Не хотите- как хотите. Завершаю работу')
        return ConversationHandler.END # Завершаем выполнение функции

    return ConversationHandler.END # Завершаем работу обработчика диалога

def GetReleaseCommand(update: Update, context):
    update.message.reply_text('lsb_release -a')
    host = RM_HOST
    port = RM_PORT
    username = RM_USER
    password = RM_PASSWORD

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname=host, username=username, password=password, port=port)
    stdin, stdout, stderr = client.exec_command('lsb_release -a')
    data = stdout.read() + stderr.read()
    client.close()
    data = str(data).replace('\\n', '\n').replace('\\t', '\t')[2:-1]
    update.message.reply_text(data) # Отправляем сообщение пользователю


def GetUnameCommand(update: Update, context):
    update.message.reply_text('uname -a')
    host = RM_HOST
    port = RM_PORT
    username = RM_USER
    password = RM_PASSWORD

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname=host, username=username, password=password, port=port)
    stdin, stdout, stderr = client.exec_command('uname -a')
    data = stdout.read() + stderr.read()
    client.close()
    data = str(data).replace('\\n', '\n').replace('\\t', '\t')[2:-1]
    update.message.reply_text(data) # Отправляем сообщение пользователю


def GetUptimeCommand(update: Update, context):
    host = RM_HOST
    port = RM_PORT
    username = RM_USER
    password = RM_PASSWORD

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname=host, username=username, password=password, port=port)
    stdin, stdout, stderr = client.exec_command('uptime')
    data = stdout.read() + stderr.read()
    client.close()
    data = str(data).replace('\\n', '\n').replace('\\t', '\t')[2:-1]
    update.message.reply_text(data) # Отправляем сообщение пользователю

def GetdfCommand(update: Update, context):
    host = RM_HOST
    port = RM_PORT
    username = RM_USER
    password = RM_PASSWORD

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname=host, username=username, password=password, port=port)
    stdin, stdout, stderr = client.exec_command('df')
    data = stdout.read() + stderr.read()
    client.close()
    data = str(data).replace('\\n', '\n').replace('\\t', '\t')[2:-1]
    update.message.reply_text(data) # Отправляем сообщение пользователю

def GetmpstatCommand(update: Update, context):
    host = RM_HOST
    port = RM_PORT
    username = RM_USER
    password = RM_PASSWORD

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname=host, username=username, password=password, port=port)
    stdin, stdout, stderr = client.exec_command('mpstat')
    data = stdout.read() + stderr.read()
    client.close()
    data = str(data).replace('\\n', '\n').replace('\\t', '\t')[2:-1]
    update.message.reply_text(data) # Отправляем сообщение пользователю

def GetfreeCommand(update: Update, context):
    host = RM_HOST
    port = RM_PORT
    username = RM_USER
    password = RM_PASSWORD

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname=host, username=username, password=password, port=port)
    stdin, stdout, stderr = client.exec_command('free')
    data = stdout.read() + stderr.read()
    client.close()
    data = str(data).replace('\\n', '\n').replace('\\t', '\t')[2:-1]
    update.message.reply_text(data) # Отправляем сообщение пользователю

def GetwCommand(update: Update, context):
    host = RM_HOST
    port = RM_PORT
    username = RM_USER
    password = RM_PASSWORD

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname=host, username=username, password=password, port=port)
    stdin, stdout, stderr = client.exec_command('w')
    data = stdout.read() + stderr.read()
    client.close()
    data = str(data).replace('\\n', '\n').replace('\\t', '\t')[2:-1]
    update.message.reply_text(data) # Отправляем сообщение пользователю

def GetauthsCommand(update: Update, context):
    host = RM_HOST
    port = RM_PORT
    username = RM_USER
    password = RM_PASSWORD

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname=host, username=username, password=password, port=port)
    stdin, stdout, stderr = client.exec_command('last -n 10 | grep -v reboot')
    data = stdout.read() + stderr.read()
    client.close()
    data = str(data).replace('\\n', '\n').replace('\\t', '\t')[2:-1]
    update.message.reply_text(data) # Отправляем сообщение пользователю

def GetCriticalCommand(update: Update, context):
    host = RM_HOST
    port = RM_PORT
    username = RM_USER
    password = RM_PASSWORD

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname=host, username=username, password=password, port=port)
    stdin, stdout, stderr = client.exec_command('journalctl -r -p crit -n 5')
    data = stdout.read() + stderr.read()
    client.close()
    data = str(data).replace('\\n', '\n').replace('\\t', '\t')[2:-1]
    update.message.reply_text(data) # Отправляем сообщение пользователю

def GetpsCommand(update: Update, context):
    host = RM_HOST
    port = RM_PORT
    username = RM_USER
    password = RM_PASSWORD

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname=host, username=username, password=password, port=port)
    stdin, stdout, stderr = client.exec_command('ps')
    data = stdout.read() + stderr.read()
    client.close()
    data = str(data).replace('\\n', '\n').replace('\\t', '\t')[2:-1]
    for i in range (0, len(data), 4096):
        update.message.reply_text(data[0:4096]) # Отправляем сообщение пользователю
        data = data[4096:]

def GetssCommand(update: Update, context):
    host = RM_HOST
    port = RM_PORT
    username = RM_USER
    password = RM_PASSWORD

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname=host, username=username, password=password, port=port)
    stdin, stdout, stderr = client.exec_command('ss')
    data = stdout.read() + stderr.read()
    client.close()
    data = str(data).replace('\\n', '\n').replace('\\t', '\t')[2:-1]
    for i in range (0, len(data), 4096):
        update.message.reply_text(data[0:4096]) # Отправляем сообщение пользователю
        data = data[4096:]

def GetAptListCommand(update: Update, context):
    update.message.reply_text('Для вывода всех пакетов(Первых ста из за ограничения телеграма) нажмите 1\nДля поиска информации о конкретном пакете напишите его имя')

    return 'GetAptList'
def GetAptList (update: Update, context):
    user_input = update.message.text # Получаем текст
    if user_input == '1':
        option='dpkg-query -f \'${binary:Package}\n\' -W'
        #option='apt list | head -n 100'
    else:
        option='apt-cache show ' + user_input
    
    host = RM_HOST
    port = RM_PORT
    username = RM_USER
    password = RM_PASSWORD

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname=host, username=username, password=password, port=port)
    stdin, stdout, stderr = client.exec_command(option)
    data = stdout.read() + stderr.read()
    client.close()
    data = str(data).replace('\\n', '\n').replace('\\t', '\t')[2:-1]
    for i in range (0, len(data), 511):
        update.message.reply_text(data[0:511]) # Отправляем сообщение пользователю
        data = data[511:]

    return ConversationHandler.END # Завершаем работу обработчика диалога    
    
def GetServicesCommand(update: Update, context):
    host = RM_HOST
    port = RM_PORT
    username = RM_USER
    password = RM_PASSWORD

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname=host, username=username, password=password, port=port)
    stdin, stdout, stderr = client.exec_command('systemctl list-units --type=service --state=running')
    data = stdout.read() + stderr.read()
    client.close()
    data = str(data).replace('\\n', '\n').replace('\\t', '\t')[2:-1]
    for i in range (0, len(data), 4096):
        update.message.reply_text(data[0:4096]) # Отправляем сообщение пользователю
        data = data[4096:]
        
def GetRepLogsCommand(update: Update, context):
    host = DB_HOST
    port = DB_PORT
    username = DB_USER
    password = DB_PASSWORD

    try:
        # Выполнение команды для получения логов
        result = subprocess.run(
            ["bash", "-c", f"cat {LOG_FILE_PATH} | grep repl | tail -n 15"],
            capture_output=True,
            text=True,
            check=True  # Проверка наличия ошибок выполнения
        )
        logs = result.stdout
        if logs:
            update.message.reply_text(f"Последние репликационные логи:\n{logs}")
        else:
            update.message.reply_text("Репликационные логи не найдены.")
    except subprocess.CalledProcessError as e:
        update.message.reply_text(f"Ошибка при выполнении команды: {e}")
    except Exception as e:
        update.message.reply_text(f"Ошибка при получении логов: {str(e)}")

def GetEmailsCommand(update: Update, context):

    connection = None
    try:
        connection = psycopg2.connect(user=DB_USER,
                                  password=DB_PASSWORD,
                                  host=DB_HOST,
                                  port=DB_PORT, 
                                  database=DB_DATABASE)

        cursor = connection.cursor()
        cursor.execute("SELECT * FROM Emails;")
        data = cursor.fetchall()
        message=''
        for row in data:
            message += ' '.join(map(str, row))+' \n'
        update.message.reply_text(message) 
        logging.info("Sucess")
    except (Exception, Error) as error:
        logging.error("Error PostgreSQL: %s", error)
    finally:
        if connection:
            cursor.close()
            connection.close()
            logging.info("Connection with PostgreSQL is closed")
        

def GetPhoneNumbersCommand(update: Update, context):
    connection = None
    try:
        connection = psycopg2.connect(user=DB_USER,
                                  password=DB_PASSWORD,
                                  host=DB_HOST,
                                  port=DB_PORT, 
                                  database=DB_DATABASE)

        cursor = connection.cursor()
        cursor.execute("SELECT * FROM Phones;")
        data = cursor.fetchall()
        message=''
        for row in data:
            message += ' '.join(map(str, row))+' \n'
        update.message.reply_text(message) 
        logging.info("Sucess")
    except (Exception, Error) as error:
        logging.error("Error PostgreSQL: %s", error)
    finally:
        if connection:
            cursor.close()
            connection.close()
            logging.info("Connection with PostgreSQL is closed")

def echo(update: Update, context):
    update.message.reply_text(update.message.text)


def main():
    updater = Updater(TOKEN, use_context=True)

    # Получаем диспетчер для регистрации обработчиков
    dp = updater.dispatcher

    # Обработчик диалога телефоны
    convHandlerFindPhoneNumbers = ConversationHandler(
        entry_points=[CommandHandler('find_phone_number', findPhoneNumbersCommand)],
        states={
            'findPhoneNumbers': [MessageHandler(Filters.text & ~Filters.command, findPhoneNumbers)],
            'findPhoneNumbersSavedb': [MessageHandler(Filters.text & ~Filters.command, findPhoneNumbersSavedb)],
        },
        fallbacks=[]
    )
        # Обработчик диалога емейл
    convHandlerFindEmail = ConversationHandler(
        entry_points=[CommandHandler('find_email', findEmailCommand)],
        states={
            'findEmail': [MessageHandler(Filters.text & ~Filters.command, findEmail)],
            'findEmailsSavedb': [MessageHandler(Filters.text & ~Filters.command, findEmailsSavedb)],
        },
        fallbacks=[]
    )
            # Обработчик диалога Паролей
    convHandlerPasswordCheck = ConversationHandler(
        entry_points=[CommandHandler('verify_password', PasswordCheckCommand)],
        states={
            'PasswordCheck': [MessageHandler(Filters.text & ~Filters.command, PasswordCheck)],
        },
        fallbacks=[]
    )
    convHandlerAptList = ConversationHandler(
        entry_points=[CommandHandler('get_apt_list', GetAptListCommand)],
        states={
            'GetAptList': [MessageHandler(Filters.text & ~Filters.command, GetAptList)],
        },
        fallbacks=[]
    )
		
	# Регистрируем обработчики команд
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("get_release", GetReleaseCommand))
    dp.add_handler(CommandHandler("get_uname", GetUnameCommand))
    dp.add_handler(CommandHandler("get_uptime", GetUptimeCommand))
    dp.add_handler(CommandHandler("get_df", GetdfCommand))
    dp.add_handler(CommandHandler("get_free", GetfreeCommand))
    dp.add_handler(CommandHandler("get_mpstat", GetmpstatCommand))
    dp.add_handler(CommandHandler("get_w", GetwCommand))
    dp.add_handler(CommandHandler("get_auths", GetauthsCommand))
    dp.add_handler(CommandHandler("get_critical", GetCriticalCommand))
    dp.add_handler(CommandHandler("get_ps", GetpsCommand))
    dp.add_handler(CommandHandler("get_ss", GetssCommand))
    dp.add_handler(CommandHandler("get_services", GetServicesCommand))
    dp.add_handler(CommandHandler("get_repl_logs", GetRepLogsCommand))
    dp.add_handler(CommandHandler("get_emails", GetEmailsCommand))
    dp.add_handler(CommandHandler("get_phone_numbers", GetPhoneNumbersCommand))
    dp.add_handler(CommandHandler("help", helpCommand))
    
    dp.add_handler(convHandlerFindPhoneNumbers)
    dp.add_handler(convHandlerFindEmail)
    dp.add_handler(convHandlerPasswordCheck)
    dp.add_handler(convHandlerAptList)

	# Регистрируем обработчик текстовых сообщений
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, echo))
		
	# Запускаем бота
    updater.start_polling()

	# Останавливаем бота при нажатии Ctrl+C
    updater.idle()


if __name__ == '__main__':
    main()