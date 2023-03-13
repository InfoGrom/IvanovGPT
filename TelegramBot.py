from email import message
from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher
from aiogram.utils import executor
from ChatGPT import ChatGPT
from DataBase import DataBase
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram import types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram import Dispatcher
import asyncio
from lang import *

class TelegramBot:
    # Инициализация бота
    def __init__(self, api_key_tg, api_keys_gpt, database_file, name_bot_command):
        self.bot = Bot(token=api_key_tg)
        self.chatgpt = ChatGPT(api_keys_gpt)
        self.database = DataBase(database_file)
        self.dp = Dispatcher(self.bot)
        self.name_bot_command = name_bot_command


        self.dp.message_handler(commands=["start"])(self.process_start_command)
        self.dp.message_handler(commands=["info"])(self.info_command_handler)
        self.dp.message_handler(commands=["help"])(self.help_command_handler)
        self.dp.message_handler(commands=["pay"])(self.pay_command_handler)
        self.dp.message_handler(commands=["admin"])(self.admin_command_handler)
        self.dp.message_handler(commands=["test"])(self.test_command_handler)
        self.dp.message_handler()(self.echo_message)
        self.dp.callback_query_handler(lambda call: call.data == 'admin_give_money')(self.admin_give_money)
        self.dp.callback_query_handler(lambda call: call.data == 'admin_add_tokens')(self.admin_add_tokens)

        # Запуск бота
        executor.start_polling(self.dp)

    # Функция регистрации пользователя в бд
    def RegisterUser(self, username, userid, firstname, lastname, banned=0, is_spam=1, balance=10, lang='ru', tokens=100, ratings=0):
        try:
            userdata = self.database.query(f"SELECT * FROM users WHERE userid='{userid}'")
            if len(userdata) <= 0:
                self.database.query(f"INSERT INTO users (username, userid, firstname, lastname, banned, is_spam) VALUES('{username}', '{userid}', '{firstname}', '{lastname}', {banned}, {is_spam})", commit=True)
                self.database.query(f"INSERT INTO settings (userid, balance, lang, tokens, ratings) VALUES('{userid}', {balance}, '{lang}', {tokens}, {ratings})", commit=True)
                return True
            return False
        except:
            return False

    # Функция провеки пользователя в базе данных
    def CheckUser(self, userid):
        userdata = self.database.query(f"SELECT * FROM users WHERE userid='{userid}'")
        if len(userdata) <= 0:
            return False
        else:
            return True

    # Функция проверки и вычитания токенов
    def CheckTokens(self, userid, text):
        userdata = self.database.query(f"SELECT * FROM settings WHERE userid='{userid}'")

        tokens = text.split()
        num_tokens = len(tokens)

        if num_tokens > userdata["tokens"]:
            return False

        balance = userdata["balance"]
        new_balance = round(balance - num_tokens/10, 2) # округление до 2 десятичных знаков
        if new_balance < 0:
            return False

        self.database.query(f"UPDATE settings SET tokens={int(userdata['tokens']) - num_tokens}, balance={new_balance} WHERE userid='{userid}'", commit=True)
        return True

    # При нажатии на старт или отправки команды /start
    async def process_start_command(self, message: types.Message):
        userid = message.from_user.id
        username = message.from_user.username
        firstname = message.from_user.first_name
        lastname = message.from_user.last_name

        # Если пользователя нету в БД, то  регистрируем его
        if(not self.CheckUser(userid)):
            self.RegisterUser(username, userid, firstname, lastname)

        # Отправляем сообщение с кнопками оплаты
        await self.bot.send_message(userid, lang['RU_COMMAND_START'].format(bot_name=self.name_bot_command,
                                    parse_mode='HTML'),
                                    )


    # Функция вызова личного кабинета пользователя /info
    async def info_command_handler(self, message: types.Message):
        user_id = message.from_user.id
        settings_user = self.GetUserSettings(user_id)

        if (settings_user["error"]):
            settings_user = settings_user["result"]
        else:
            return

        balance = settings_user["balance"]
        lang = settings_user["lang"]
        tokens = settings_user["tokens"]
        ratings = settings_user ["ratings"]
        text = f"\n\n\n<b>👤 Мой аккаунт:</b>\n\n<b> ID:</b> {user_id}\n<b> Имя:</b> <code>{message.from_user.first_name}</code>\n<b> Рейтинг в чатах:</b> <code>+{ratings}</code>\n\n<b>🖥 Мой профиль:</b>\n<b>├ Партнерский счет:</b> <code>No</code><b>\n├ Осталось:</b> <code>{tokens}</code> токенов\n<b>└ Мой баланс:</b> <code>{balance}</code> RUB\n\n💳 <b>Продлить подписку:</b> /pay"

        # Отправляем сообщение с кнопками оплаты
        await self.bot.send_message(
            chat_id=user_id,
            text=text,
            parse_mode='HTML',
        ) 

    # Функция ответа на команду /help
    async def help_command_handler(self, message: types.Message):
        user_id = message.from_user.id
        settings_user = self.GetUserSettings(user_id)

        if (settings_user["error"]):
            settings_user = settings_user["result"]
        else:
            return
        text = f"🆘 <code>{message.from_user.first_name}</code>, <b>Вам нужна помощь?</b>\n\n<b>Пожалуйста, обратите внимание, что в поддержке классифицированные специалисты. Мы постараемся помочь как можно быстрее, но ожидание может занять некоторое время.</b>\n\n<b>График работы администраторов: 09:00-18:00 по московскому времени.</b>\n\n⚠️ <b>Техническая поддержка:</b>\n\nОбщий чат: @infogrom_Forum.\nВаш идентификатор аккаунта:\n<b>Имя:</b> <code>{message.from_user.first_name}</code>\n<b>ID:</b> <code>{message.from_user.id}</code>\n\nЧтобы связаться с тех. поддержкой для решения каких либо вопросов, отправтье боту сообщение «Помощь» или нажмите на кнопку ниже:"
        
        # Создаем объекты кнопок оплаты
        support_button = types.InlineKeyboardButton(text="🆘 Перейти в тех. поддержку", url="https://t.me/InfoGrom_Forum/108")

        # Создаем объект клавиатуры с кнопками оплаты
        payment_keyboard = types.InlineKeyboardMarkup(row_width=1)
        payment_keyboard.add(support_button)

        # Отправляем сообщение с кнопками оплаты
        await self.bot.send_message(
            chat_id=user_id,
            text=text,
            parse_mode='HTML',
            reply_markup=payment_keyboard
        ) 
        
    # Функция ответа на команду /pay
    async def pay_command_handler(self, message: types.Message):
        user_id = message.from_user.id
        settings_user = self.GetUserSettings(user_id)

        if (settings_user["error"]):
            settings_user = settings_user["result"]
        else:
            return

        text = f"<b>💳 Управление подпиской бота:</b>\n\n✅ Подписка — открывает доступ к запросам на сервера «ChatGPT», тем самым увеличивает лимит токенов. Выберите тариф и после оплаты, перейдите по кнопке «🆘 Перейти в тех. поддержку», напишите Ваше Имя, или @username, сумму и количество токенов, чтобы Администратор обновил Ваш личный кабинет. Если у Вас какие-то вопросы, напишите мне @IvanovGPT и мы что-нибудь придумаем:"

        # Создаем объекты кнопок оплаты
        payment_button_1 = types.InlineKeyboardButton(text="500 токенов за 59 руб.", url="https://oplata.qiwi.com/form?invoiceUid=bbca21dd-ae7b-4acf-ad33-14b127906808&successUrl=https%3A%2F%2Ft.me%2FIvanovGPTbot")
        payment_button_2 = types.InlineKeyboardButton(text="1000 токенов за 99 руб.", url="https://oplata.qiwi.com/form?invoiceUid=9087c35a-17a1-482f-91d7-294d59effe0c&successUrl=https%3A%2F%2Ft.me%2FIvanovGPTbot")
        payment_button_3 = types.InlineKeyboardButton(text="2000 токенов за 199 руб.", url="https://oplata.qiwi.com/form?invoiceUid=fa13e3ff-dbab-4b3b-8d24-7ed6ebe7847e&successUrl=https%3A%2F%2Ft.me%2FIvanovGPTbot")
        payment_button_4 = types.InlineKeyboardButton(text="5000 токенов за 499 руб.", url="https://oplata.qiwi.com/form?invoiceUid=e592f04a-a2ef-4a27-be59-9594d1159ac9&successUrl=https%3A%2F%2Ft.me%2FIvanovGPTbot")
        support_button = types.InlineKeyboardButton(text="🆘 Перейти в тех. поддержку", url="https://t.me/InfoGrom_Forum/108")



        # Создаем объект клавиатуры с кнопками оплаты
        payment_keyboard = types.InlineKeyboardMarkup(row_width=2)
        payment_keyboard.add(payment_button_1, payment_button_2, payment_button_3, payment_button_4)
        payment_keyboard.add(support_button)

        # Отправляем сообщение с кнопками оплаты
        await self.bot.send_message(
            chat_id=user_id,
            text=text,
            parse_mode='HTML',
            reply_markup=payment_keyboard
        ) 

    def GetUserSettings(self, userid):
        userdata = self.database.query(f"SELECT * FROM settings WHERE userid={userid}")
        if len(userdata) <= 0:
            return {"result": userdata, "error": False}
        else:
            return {"result": userdata, "error": True}

    # Функция ответа на сообщение
    async def echo_message(self, message: types.Message):
        message_id = message.message_id
        rq = message.text
        userid = message.from_user.id
        username = message.from_user.username
        firstname = message.from_user.first_name
        lastname = message.from_user.last_name
        if not self.CheckUser(userid):
            self.RegisterUser(username, userid, firstname, lastname)

        user_id = message.from_user.id
        settings_user = self.GetUserSettings(user_id)

        if (settings_user["error"]):
            settings_user = settings_user["result"]
        else:
            return

        ratings = settings_user ["ratings"]

        me = await self.bot.get_me()

        # Ответное сообщение пользователю на реакцию:
        if rq in ['Спасибо', '+']:
            if message.reply_to_message and message.reply_to_message.from_user.username:
                # получаем имя пользователя, отправившего благодарность
                #recipient_username = message.reply_to_message.from_user.username
                # получаем id пользователя, которому отправлена благодарность
                recipient_userid = message.reply_to_message.from_user.id
                # формируем текст сообщения с упоминанием пользователя
                text = f"👍 <code>{username}</code> <b>выразил(а) Вам благодарность! <code>({ratings})</code></b>"
                # отправляем сообщение с упоминанием пользователя и парсингом HTML
                await self.bot.send_message(
                    chat_id=message.chat.id,
                    text=text,
                    reply_to_message_id=message.reply_to_message.message_id,
                    parse_mode='HTML'
                )

                # увеличиваем количество ratings в таблице settings базы данных на 1
                self.database.query(f"UPDATE settings SET ratings=ratings+1 WHERE userid={recipient_userid}", commit=True)
                # выводим сообщение об успешной отправке
                print(f"({username} -> bot): {rq}\n(bot -> {username}): {username} выразил(а) Вам благодарность!")
                return
            
        # Ответное сообщение пользователю на Ссылку:
        if message.text == 'Ссылка':
            keyboard_markup = types.InlineKeyboardMarkup(row_width=2)
            url_button = types.InlineKeyboardButton(text='✅ ДА', url='https://t.me/IvanovGPTbot')
            delete_button = types.InlineKeyboardButton(text='❌ НЕТ', callback_data='delete')
            keyboard_markup.add(url_button, delete_button)
            await self.bot.send_message(
                chat_id=message.chat.id,
                text='↩️ Вы искали ссылку на Бота?',
                reply_to_message_id=message.message_id,
                reply_markup=keyboard_markup
            )

        # Ответное сообщение пользователю на помощь:
        if message.text == 'Помощь':
            keyboard_markup = types.InlineKeyboardMarkup(row_width=2)
            url_button = types.InlineKeyboardButton(text='✅ ДА', url='https://t.me/InfoGrom_Forum/108')
            delete_button = types.InlineKeyboardButton(text='❌ НЕТ', callback_data='delete')
            keyboard_markup.add(url_button, delete_button)
            await self.bot.send_message(
                chat_id=message.chat.id,
                text='🆘 Вам чем-то помочь?',
                reply_to_message_id=message.message_id,
                reply_markup=keyboard_markup
            )

        # С запросом ключевого слова "Иванов":
        if self.name_bot_command in rq:
            if self.CheckTokens(userid, rq):
                await self.bot.send_message(chat_id=message.chat.id,
                                            text="⏳ <b>Ожидайте...</b>",
                                            reply_to_message_id=message.message_id,
                                            parse_mode='HTML')
                # Анимация "Печатает":
                await self.bot.send_chat_action(chat_id=message.chat.id, action='typing')
                generated_text = self.chatgpt.getAnswer(message=rq.replace(self.name_bot_command, ''), lang="ru", max_tokens=1000, temperature=0., top_p=1, frequency_penalty=0, presence_penalty=0, engine_model="text-davinci-003")
                await self.bot.edit_message_text(chat_id=message.chat.id,
                                                text=generated_text["message"],
                                                message_id=message.message_id+1)
                print(f"(@{username} -> bot): {rq}\n(bot -> @{username}): {generated_text['message']}")
            else:
                await self.bot.send_message(chat_id=message.chat.id, text=f"🔴 Извините <code>{message.from_user.first_name}</code>, бесплатный лимит запросов исчерпан... Вы потратили 100 демо - токенов. Чтобы увеличить лимит запросов, перейдите в бота и отправьте команду /pay", reply_to_message_id=message.message_id)
                print(f"(@{username} -> bot): {rq}\n(bot -> @{username}):🔴 Извините <code>{message.from_user.first_name}</code>, бесплатный лимит запросов исчерпан... Вы потратили 100 демо - токенов. Чтобы увеличить лимит запросов, перейдите в бота и отправьте команду /pay")
 
    def is_user_admin(self, user_id):
        try:
            userdata = self.database.query(f"SELECT * FROM users WHERE userid={user_id}")
            if len(userdata) > 0 and userdata['admin'] == 1:
                return True
            return False
        except:
            return False

    # При нажатии на старт или отправки команды /test
    async def test_command_handler(self, message: types.Message):
        message_id = message.message_id
        rq = message.text
        userid = message.from_user.id
        username = message.from_user.username
        firstname = message.from_user.first_name
        lastname = message.from_user.last_name

        user, money = message.get_args().split()

        # Если пользователя нету в БД, то  регистрируем его
        if(not self.CheckUser(userid)):
            self.RegisterUser(username, userid, firstname, lastname)
        await self.bot.send_message(chat_id=message.chat.id, text=f"user = {user}\nmoney = {money}", reply_to_message_id=message_id)

    # При нажатии на старт или отправки команды /admin
    async def admin_command_handler(self, message: types.Message):
        message_id = message.message_id
        rq = message.text
        userid = message.from_user.id
        username = message.from_user.username
        firstname = message.from_user.first_name
        lastname = message.from_user.last_name

        # Если пользователя нету в БД, то  регистрируем его
        if(not self.CheckUser(userid)):
            self.RegisterUser(username, userid, firstname, lastname)
        await self.bot.send_message(chat_id=message.chat.id, text="Выберете действие:", reply_to_message_id=message_id, reply_markup=self.admin_buttons())

    # Кнопки админки
    def admin_buttons(self):
        buttons = types.InlineKeyboardMarkup(row_width=2)
        buttons.add(
            types.InlineKeyboardButton(text="💰 Выдать деньги", callback_data='admin_give_money'),
            types.InlineKeyboardButton(text="🔸 Выдать токены", callback_data='admin_add_tokens')
            )
        buttons.row(
            types.InlineKeyboardButton(text="📩 Рассылка", callback_data='admin_spam')
            )
        buttons.row(
            types.InlineKeyboardButton(text="❌ Забанить", callback_data='admin_ban'),
            types.InlineKeyboardButton(text="✅ Разбанить", callback_data='admin_unban')
            )
        return buttons

    # Функция по выдаче денег
    async def admin_give_money(self, call: types.CallbackQuery):
        await self.bot.send_message(chat_id=call.message.chat.id, text="Введите формате: <code>/money @username количество</code>", parse_mode='HTML')

    # Функция по выдаче денег
    async def admin_add_tokens(self, call: types.CallbackQuery):
        await self.bot.send_message(chat_id=call.message.chat.id, text="Введите формате: <code>/money @username количество</code>", parse_mode='HTML')