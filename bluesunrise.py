import telebot
from config import *
from telebot import types
from telebot.types import Message
import logging
from gpt import GPT


token = ""
bot = telebot.TeleBot(token)

max_letters = MAX_TOKENS

# Словарь для хранения задач пользователей и ответов GPT
user_history = {}
current_options = {}
users = {
    "id": "",
    "question": "",
    "answer": "",
    "subject": "",
    "level": "",
}

gpt = GPT()
#create_table("users")
#create_db()

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    filename="log_file.txt",
    filemode="w",
)


def make_keyboard(buttons_list):
    keyboard = types.ReplyKeyboardMarkup(row_width=3, resize_keyboard=True, one_time_keyboard=True)
    keyboard.add(*buttons_list)
    return keyboard

def solve(message: Message):
    if(message.text == "Решить"):return "Решить" in message.text
    else: bot.send_message(message.chat.id, "Я не распознал твой ответ, используй кнопку")

@bot.message_handler(commands=["start"])
def start(message: Message):
    global current_options
    logging.debug("Пользователь начал работу с ботом")
    bot.send_message(message.chat.id, f"Приветствую вас, {message.from_user.full_name}! Если вы попали сюда, значит вам была предоставлена "
                                      "секретная ссылка, которая достаётся только участникам тайного эксперимента Fazbear Ent.: "
                                      "'Синяя заря'. А значит, вы принимаете участие в нём. Что ж, поздравляю!\n Модель эксперимента: "
                                      "B1D1. Первый прототип. Пока задачи бота-ИИ состоят в решении математических задач/примеров. "
                                      "P.S. Используя этого бота, вы предоставляете свои личные данные компании Fazbear Ent. "
                                      "За ущерб, нанесённый этим данным, компания ответственности не несёт 🤷‍♂️.",
                     reply_markup=make_keyboard(["Решить"]))
    bot.register_next_step_handler(message, solve_task)
    
    users["id"] = str(message.from_user.id)

@bot.message_handler(commands=['help'])
def support(message: Message):
    logging.debug("Пользователь нажал /help")
    bot.send_message(message.chat.id, "Просто нажми на кнопку: 'Решить', а потом пиши условие своей задачи. В другом случае "
                                      "пиши команду /solve_task")

@bot.message_handler(commands=['solve_task'])
def solvee__task(message: Message):
    logging.debug("Пользователь нажал /solve_task")
    bot.register_next_step_handler(message, solve_task)


@bot.message_handler(commands=["about"])
def about(message: Message):
    logging.debug("Пользователь нажал /about")
    bot.send_message(message.chat.id, text1)


@bot.message_handler(content_types=["text"], func=solve)
def solve_task(message: Message):
    
    logging.debug("Пользователь начинает обращение к боту")
    bot.send_message(message.chat.id, "Выберите предмет 🙂:", reply_markup=make_keyboard(["математика", "физика"]))
    bot.register_next_step_handler(message, choose_subject)


def choose_subject(message):
    
    bot.send_message(message.chat.id, "Выберите уровень ответа:", reply_markup=make_keyboard(["лёгкий", "продвинутый"]))
    bot.register_next_step_handler(message, choose_level)
    
    users["subject"] = message.text

def choose_level(message):
   
    bot.send_message(message.chat.id, "Напишите ваш запрос")
    bot.register_next_step_handler(message, get_promt)
    
    users["level"] = message.text

def continue_filter(message: Message):
    button_text = 'Продолжить решение'
    return message.text == button_text


# Получение задачи от пользователя или продолжение решения
@bot.message_handler(func=continue_filter)
def get_promt(message):
    
    global current_options
    logging.debug("Пользователь отправил запрос")
    user_id = message.from_user.id

    if message.content_type != "text":
        bot.send_message(user_id, "Упс, ты что-то не то прислал. Надо только текстом!")
        bot.register_next_step_handler(message, get_promt)
        return

    # Получаем текст сообщения от пользователя
    user_request = message.text
    users["question"] = message.text

    gpt.count_tokens(user_request)

    #if len(user_request) > MAX_TOKENS:
        #bot.send_message(user_id, "Ой, твоё сообщение превышает лимит(\nИсправь запрос")
        #bot.register_next_step_handler(message, get_promt)
        #return

    if user_id not in user_history or user_history[user_id] == {}:
       
        if users["subject"] not in ["математика", "физика"]:
            bot.send_message(user_id, "Ты не ввёл предмет, начинаем сначала.")
            start(message)
        if users["level"] not in ["лёгкий", "сложный"]:
            bot.send_message(user_id, "Ты не ввёл уровень, начинаем сначала.")
            start(message)

        


        # Сохраняем промт пользователя и начало ответа GPT в словарик users_history
        user_history[user_id] = {
                'system_content': f'Ты - дружелюбный помощник для решения задач по  {users["subject"]}. Давай ответ {users["level"]} языком.',
                'user_content': user_request,
                'assistant_content': "Решим задачу по шагам: "
            }

    prompt = gpt.make_promt(user_history[user_id])
    resp = gpt.send_request(prompt)


    answer = gpt.process_resp(resp)
    #execute_query(f"INSERT INTO users (user_id, subject, level, task, answer) VALUES ({user_id}, норм, ок,"
                  #f"'{user_request}', '{answer[1]}'")
    user_history[user_id]['assistant_content'] += answer[1]

    bot.send_message(user_id, text=user_history[user_id]['assistant_content'],
                     reply_markup=make_keyboard(["Продолжить решение", "Завершить решение"]))
    users["answer"] = answer
    print(users)


def end_filter(message: Message):
    return message.text == 'Завершить решение'



@bot.message_handler(content_types=['text'], func=end_filter)
def end_task(message: Message):
    logging.debug("Решение завершеноbluesunrise.py")
    user_id = message.from_user.id
    bot.send_message(user_id, "Текущие решение завершено")
    user_history[user_id] = {}
    solve_task(message)

@bot.message_handler(commands=["debug"])
def debug_(message):
    with open("log_file.txt", "rb") as f:
        bot.send_document(message.chat.id, f)














bot.polling()


