import datetime
import random
import sqlite3
import states
import config
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import asyncio

bot = Bot(token=config.bot_token)
dp = Dispatcher(bot, storage=MemoryStorage())
bdcon = sqlite3.connect("maindb.db")
cursor = bdcon.cursor()


cursor.execute("""
    CREATE TABLE IF NOT EXISTS users(
        chat_id int not null,
        rank int default -1,
        paytag text default "#010101",
        percent float default 50,
        wallet text default 'Не установлен'
    )
""")
cursor.execute("""
    CREATE TABLE IF NOT EXISTS mentors(
        chat_id int not null,
        label text default '',
        info text default ''
    )
""")
cursor.execute("""
    CREATE TABLE IF NOT EXISTS profits(
        owner_id int,
        count float,
        profit_date date
    )
""")


def new_paytag() -> str:
    a = "qwertyuiopasdfghjklzxcvbnmQWERTYUIOPASDFGHJKLZXCVBNM1234567890"
    tag = "#"
    for i in range(1, 6):
        tag += a[random.Random().randint(a=0, b=(len(a) - 1))]
    return tag


def get_user(chat_id):
    user = cursor.execute("select * from users where chat_id = ?", (chat_id,)).fetchone()
    return user


def main_menu():
    menu = InlineKeyboardMarkup()
    menu.row(
        InlineKeyboardButton(text="Мой профиль 🧑🏿‍🦱", callback_data="menu_profile")
    )
    menu.row(
        InlineKeyboardButton(text="Мануалы 📘", callback_data="menu_manual")
    )
    menu.row(
        InlineKeyboardButton(text="Взять PayPal 🅿️", callback_data="menu_paypal"),
        InlineKeyboardButton(text="Взять IBAN 🏦", callback_data="menu_iban")
    )
    menu.row(
        InlineKeyboardButton(text="Менторы 👩🏿‍💻", callback_data="menu_mentors")
    )
    menu.row(
        InlineKeyboardButton(text="Помощь 🚨", url=config.help_link),
        InlineKeyboardButton(text="Чаты 👋🏿", callback_data="menu_chats")
    )
    menu.row(
        InlineKeyboardButton(text="Чеки/доки/отрисовки 👨🏿‍🎨", url=config.drawing_link)
    )
    return menu


def paypal_menu():
    menu = InlineKeyboardMarkup()
    menu.row(
        InlineKeyboardButton(text="UKR", callback_data="0_get_paypal:UKR"),
        InlineKeyboardButton(text="F/F", callback_data="0_get_paypal:F/F")
    )
    menu.row(
        InlineKeyboardButton(text="✋🏿 Назад", callback_data="main_menu")
    )
    return menu


def iban_menu():
    menu = InlineKeyboardMarkup()
    menu.row(
        InlineKeyboardButton("Взять 🫴🏿", callback_data="get_iban")
    )
    return menu


def mentor_menu():
    menu = InlineKeyboardMarkup()
    mentors = cursor.execute("select * from mentors").fetchall()
    for i in mentors:
        menu.row(
            InlineKeyboardButton(
                text=f"{i[1]}", callback_data=f"check_mentor:{i[0]}"
            )
        )
    menu.row(InlineKeyboardButton(text="✋🏿 Назад", callback_data="main_menu"))
    return menu


def profile_menu(owner):
    menu = InlineKeyboardMarkup()
    menu.row(
        InlineKeyboardButton(text="🗂 Мои профиты", callback_data=f"show_profits:{owner}:1"),
    )
    menu.row(
        InlineKeyboardButton(
            text="Мой Кошелёк 💸", callback_data=f"open_wallet:{owner}"
        ),
        InlineKeyboardButton(
            text="Мой PAY-TAG 🅿️", callback_data=f"show_paytag:{owner}"
        )
    )
    menu.row(InlineKeyboardButton(text="✋🏿 Назад", callback_data="main_menu"))
    return menu


def wallet_menu(owner):
    menu = InlineKeyboardMarkup()
    menu.row(InlineKeyboardButton(text="✒️ Изменить адрес кошелька", callback_data=f"change_wallet:{owner}"))
    menu.row(InlineKeyboardButton(text="✋🏿 Назад", callback_data="main_menu"))
    return menu


def paytag_menu(owner):
    menu = InlineKeyboardMarkup()
    menu.row(InlineKeyboardButton(text="✒️ Изменить PAY-TAG", callback_data=f"change_paytag:{owner}"))
    menu.row(InlineKeyboardButton(text="✋🏿 Назад", callback_data="main_menu"))
    return menu


def chat_link_menu():
    menu = InlineKeyboardMarkup(row_width=1)
    menu.add(
        InlineKeyboardButton(text="Чат 🏃‍♂️", url=config.chat_link),
        InlineKeyboardButton(text="Выплаты 💸", url=config.withdraw_link),
        InlineKeyboardButton(text="✋🏿 Назад", callback_data="main_menu")
    )
    return menu


@dp.callback_query_handler(lambda c: c.data.startswith("show_profits"))
async def on_sp(c: types.CallbackQuery):
    user_id = int(c.data.split(":")[1])
    page_num = int(c.data.split(":")[2])
    profits = cursor.execute("select * from profits where owner_id = ?", (user_id,)).fetchall()
    _text = ""
    for q in range((page_num - 1) * 8, page_num * 8):
        if len(profits) - 1 < q:
            break
        i = profits[q]
        _text += f"{i[1]}€ {i[2]}\n"
    await bot.send_message(
        c.message.chat.id,
        f"💵 Ваши профиты:\n\n{_text}"
    )


@dp.callback_query_handler(lambda c: c.data.startswith("open_wallet"))
async def on_op(c: types.CallbackQuery):
    user_id = int(c.data.split(":")[1])
    user = get_user(user_id)
    await bot.edit_message_text(
        chat_id=c.message.chat.id,
        message_id=c.message.message_id,
        text=f"💸 Мой кошелёк:\n\n <i>{user[4]}</i>",
        parse_mode="HTML",
        reply_markup=wallet_menu(c.message.chat.id)
    )


@dp.callback_query_handler(lambda c: c.data.startswith("show_paytag"))
async def on_sp(c: types.CallbackQuery):
    user_id = int(c.data.split(":")[1])
    user = get_user(user_id)
    await bot.edit_message_text(
        chat_id=c.message.chat.id,
        message_id=c.message.message_id,
        text=f"🅿️ Мой PAY-TAG:\n\n <b>{user[2]}</b>\n\n<b>Данный Тег будет показан\nв канале выплат!</b>",
        parse_mode="HTML",
        reply_markup=paytag_menu(c.message.chat.id)
    )


@dp.message_handler(lambda msg: msg.chat.id == config.admin_chat_id, commands=['userinfo'])
async def on_w(msg: types.Message):
    users = cursor.execute("select * from users").fetchall()
    if len(msg.text.split(' ')) < 2 or msg.text.split(' ')[1] == 1:
        page_num = 1
    else:
        page_num = msg.text.split(' ')[1]
    _text = f"Список пользователей. Страница {page_num}.\n"
    for i in range((page_num-1)*15, page_num*15):
        if len(users) <= i:
            break
        profit_summ = cursor.execute('select sum(count) from profits where owner_id = ?', (users[i][0],)).fetchone()[0]
        if profit_summ is None:
            profit_summ = 0
        profit_count = len(cursor.execute('select * from profits where owner_id = ?', (users[i][0],)).fetchall())
        _text += f"\nID: {users[i][0]}, PAYTAG: {users[i][2]} Wallet: {users[i][4]} Percent: {users[i][3]} " \
                 f"Кол-во профитов: {profit_count} На сумму: {profit_summ}"
    _text += "\n\nДругие страницы: /wallets <номер страницы>\n" \
             "Чтобы изменить чей-то номер кошелька напишите: /changewallet <user_id> <адрес кошелька>\n" \
             "Чтобы изменить чей-то процент напишите: /changepercent <user_id> <процент>"
    await bot.send_message(msg.chat.id, _text)


@dp.message_handler(lambda msg: msg.chat.id == config.admin_chat_id, commands=['changewallet'])
async def on_w(msg: types.Message):
    if len(msg.text.split(' ')) < 3:
        await bot.send_message(msg.chat.id, "Недостаточно аргументов в команде.")
        return
    if not msg.text.split(' ')[1].isdigit():
        await bot.send_message(msg.chat.id, "Неверный айди пользователя.")
        return
    if get_user(int(msg.text.split(' ')[1])) is None:
        await bot.send_message(msg.chat.id, "Пользователя с указанный айди нет в базе.")
        return
    cursor.execute("update users set wallet = ? where chat_id = ?", (msg.text.split(' ')[2], int(msg.text.split(' ')[1])))
    bdcon.commit()
    await bot.send_message(msg.chat.id, "Адрес кошелька успешно изменен!")


@dp.message_handler(lambda msg: msg.chat.id == config.admin_chat_id, commands=['changepercent'])
async def on_w(msg: types.Message):
    if len(msg.text.split(' ')) < 3:
        await bot.send_message(msg.chat.id, "Недостаточно аргументов в команде.")
        return
    if not msg.text.split(' ')[1].isdigit():
        await bot.send_message(msg.chat.id, "Неверный айди пользователя.")
        return
    if get_user(int(msg.text.split(' ')[1])) is None:
        await bot.send_message(msg.chat.id, "Пользователя с указанный айди нет в базе.")
        return
    try:
        f = float(msg.text.split(' ')[2]) + 1.0
        print(f"check {f}")
    except:
        await bot.send_message(msg.chat.id, "Неверно указан процент.")
        return
    cursor.execute("update users set percent = ? where chat_id = ?", (float(msg.text.split(' ')[2]), int(msg.text.split(' ')[1])))
    bdcon.commit()
    await bot.send_message(msg.chat.id, "Процент пользователя успешно изменен!")


@dp.message_handler(lambda msg: msg.chat.id == config.admin_chat_id or msg.chat.id in config.notifications_chats, commands=['stats'])
async def on_chats(msg: types.Message):
    profits = cursor.execute("select * from profits group by owner_id").fetchall()
    top = []
    all_cash = 0.0
    for i in profits:
        find = False
        all_cash += i[1]
        for t in top:
            if t["owner"] == i[0]:
                find = True
                t["balance"] += i[1]
                break
        if not find:
            top.append({"owner": i[0], "balance": i[1]})
    s = sorted(top, key=lambda _t: _t["balance"])
    _text = "Топ воркеров за всё время:"
    for q in range(0, 9):
        if len(s) - 1 < q:
            break
        i = s[q]
        if i["balance"] == 0:
            continue
        else:
            paytag = cursor.execute(
                "select paytag from users where chat_id = ?", (i["owner"],)
            ).fetchone()[0]
            _text += f"\n{q+1}. {paytag} : {i['balance']}€"
    _text += f"\n\nОбщая касса: {all_cash}€"
    await bot.send_message(msg.chat.id, _text)


@dp.message_handler(lambda msg: msg.chat.id == config.admin_chat_id or msg.chat.id in config.notifications_chats)
async def on_tr(msg: types.message):
    pass


@dp.message_handler(lambda msg: get_user(msg.chat.id) is not None and int(get_user(msg.chat.id)[1]) >= 1, commands=['start'])
async def on_start(msg: types.Message):
    await bot.send_message(msg.chat.id, "BAPE TEAM", reply_markup=main_menu())


@dp.message_handler(lambda msg: get_user(msg.chat.id) is None)
async def on_new_user(msg: types.Message, state: FSMContext):
    print(msg.chat.id)
    cursor.execute(
        "insert into users (chat_id) values (?)", (msg.chat.id,)
    )
    bdcon.commit()
    await bot.send_message(msg.chat.id, "Здравствуйте, с какой тимы вы пришли?")
    await state.set_state(states.Form_state.q1)


@dp.callback_query_handler(lambda c: c.data.startswith("check_mentor"))
async def on_cm(c: types.CallbackQuery):
    mentor_id = int(c.data.split(':')[1])
    mentor = cursor.execute("select * from mentors where chat_id = ?", (mentor_id,)).fetchone()
    menu = InlineKeyboardMarkup()
    menu.add(InlineKeyboardButton(text="Выбрать", callback_data=f"chose_mentor:{mentor_id}"))
    menu.add(InlineKeyboardButton(text="Отмена", callback_data="mentor_list"))
    await bot.edit_message_text(
        chat_id=c.message.chat.id,
        message_id=c.message.message_id,
        text=mentor[2],
        reply_markup=menu
    )


@dp.callback_query_handler(lambda c: c.data.startswith("chose_mentor"))
async def on_cm(c: types.CallbackQuery):
    mentor_id = int(c.data.split(':')[1])
    user = get_user(c.message.chat.id)
    if c.message.from_user.username is None:
        username = "Юзернейм не указан."
    else:
        username = c.message.from_user.username
    await bot.send_message(mentor_id, f"Новая заявка на наставничество!\nТег: {user[2]}\nСвязь: @{username}")
    await c.answer(text="🥷 Наставник получил ваш запрос!", show_alert=True)


@dp.message_handler(commands="imentor")
async def on_m(msg: types.message, state: FSMContext):
    await bot.send_message(msg.chat.id, "Запрос на становление ментором отправлен!")
    user = get_user(msg.chat.id)
    profits = cursor.execute("select * from profits where owner_id = ?", (msg.chat.id,)).fetchall()
    menu = InlineKeyboardMarkup()
    menu.add(
        InlineKeyboardButton(text="✅ Принять", callback_data=f"accept_mentor:{msg.chat.id}"),
        InlineKeyboardButton(text="❌ Отклонить", callback_data=f"decline_mentor")
    )
    profits_count = len(profits)
    profits_sum = 0
    for p in profits:
        profits_sum += p[1]
    await bot.send_message(
        config.admin_chat_id,
        f"Заявка на становление ментором!\n"
        f"PayTag: {user[2]}\n"
        f"Имеет: {profits_count} профит(ов) на сумму {profits_sum}",
        reply_markup=menu
    )


@dp.callback_query_handler(lambda c: c.data.startswith("accept_mentor"))
async def on_m(c: types.CallbackQuery):
    user_id = int(c.data.split(':')[1])
    await bot.edit_message_text(
        chat_id=c.message.chat.id,
        message_id=c.message.message_id,
        text="Заявка на менторство была одобрена."
    )
    await bot.send_message(chat_id=user_id, text="Заявка на менторство была одобрена!\n"
                                                 "Укажите текст, который будет виден в "
                                                 "строке поиска ментора (до 60 символов")
    await dp.current_state(chat=user_id).set_state(states.MentorState.label)


@dp.message_handler(state=states.MentorState.label)
async def on_label(msg: types.Message, state: FSMContext):
    if len(msg.text) > 60:
        await bot.send_message(msg.chat.id, "Слишком длинный текст!")
        return
    await state.set_state(states.MentorState.info)
    await state.update_data({"label": msg.text})
    await bot.send_message(msg.chat.id, "Теперь укажите подробную информацию о себе (до 500 символов)")


@dp.message_handler(state=states.MentorState.info)
async def on_label(msg: types.Message, state: FSMContext):
    if len(msg.text) > 500:
        await bot.send_message(msg.chat.id, "Слишком длинный текст!")
        return
    label = (await state.get_data())["label"]
    cursor.execute("insert into mentors values (?, ?, ?)", (msg.chat.id, label, msg.text))
    bdcon.commit()
    await state.finish()
    await bot.send_message(msg.chat.id, "Поздравляю, вы теперь ментор! 🎉")


@dp.message_handler(content_types=['text'], state=states.Form_state.q1)
async def on_q1(msg: types.message, state: FSMContext):
    await state.update_data({"q1": msg.text})
    await bot.send_message(msg.chat.id, "Есть ли у вас опыт в данной сфере?")
    await state.set_state(states.Form_state.q2)


@dp.message_handler(content_types=['text'], state=states.Form_state.q2)
async def on_q1(msg: types.message, state: FSMContext):
    await state.update_data({"q2": msg.text})
    await bot.send_message(msg.chat.id, "Откуда вы о нас узнали??")
    await state.set_state(states.Form_state.q3)


@dp.message_handler(content_types=['text'], state=states.Form_state.q3)
async def on_q1(msg: types.message, state: FSMContext):
    await state.update_data({"q3": msg.text})
    questions = await state.get_data()
    await state.finish()
    await bot.send_message(msg.chat.id, "☑️ Заявка отправлена на рассмотрение администрацией!")
    menu = InlineKeyboardMarkup()
    menu.row(
        InlineKeyboardButton(text="✅ Принять", callback_data=f"accept_user:{msg.chat.id}"),
        InlineKeyboardButton(text="❌ Отклонить", callback_data=f"decline_user:{msg.chat.id}")
    )
    await bot.send_message(config.admin_chat_id,
                           f"Новая заявка!\nСодержание:\n\n"
                           f"1. {questions['q1']}\n2. {questions['q2']}\n3. {questions['q3']}",
                           reply_markup=menu)


@dp.callback_query_handler(lambda c: c.data.startswith("accept_user"))
async def on_accept(c: types.CallbackQuery):
    user_id = int(c.data.split(':')[1])
    await bot.edit_message_text(
        chat_id=c.message.chat.id,
        message_id=c.message.message_id,
        text=c.message.text + "\n\n✅ Заявка принята!"
    )
    cursor.execute("update users set rank = 1, paytag = ? where chat_id = ?", (new_paytag(), user_id))
    bdcon.commit()
    await bot.send_message(user_id, "✅ Ваша заявка была принята!", reply_markup=main_menu())


@dp.callback_query_handler(lambda c: c.data.startswith("decline_user"))
async def on_accept(c: types.CallbackQuery):
    await bot.edit_message_text(
        chat_id=c.message.chat.id,
        message_id=c.message.message_id,
        text=c.message.text + "\n\n❌ Заявка отклонена!!"
    )


@dp.callback_query_handler(lambda c: c.data.startswith("change_wallet"))
async def on_cw(c: types.CallbackQuery, state: FSMContext):
    await bot.send_message(
        c.message.chat.id,
        "💷 Укажите новый адрес кошелька"
    )
    await state.set_state(states.ChangeState.wallet)


@dp.callback_query_handler(lambda c: c.data.startswith("change_paytag"))
async def on_cp(c: types.CallbackQuery, state: FSMContext):
    await bot.send_message(
        c.message.chat.id,
        "🅿️ Укажите новый PAY-TAG"
    )
    await state.set_state(states.ChangeState.paytag)


@dp.message_handler(state=states.ChangeState.wallet)
async def on_cw(msg: types.Message, state: FSMContext):
    await bot.send_message(
        msg.chat.id,
        "✅ Адрес кошелька успешно изменен!"
    )
    cursor.execute("update users set wallet = ? where chat_id = ?", (msg.text, msg.chat.id))
    bdcon.commit()
    await state.finish()


@dp.message_handler(state=states.ChangeState.paytag)
async def on_cw(msg: types.Message, state: FSMContext):
    await bot.send_message(
        msg.chat.id,
        "✅ 🅿️PAY-TAG успешно изменен!"
    )
    cursor.execute("update users set paytag = ? where chat_id = ?", ("#" + msg.text, msg.chat.id))
    bdcon.commit()
    await state.finish()


@dp.callback_query_handler(lambda c: c.data.startswith("0_get_paypal"))
async def on_pp(c: types.CallbackQuery):
    wallet_name = c.data.split(':')[1]
    menu = InlineKeyboardMarkup()
    menu.row(
        InlineKeyboardButton(text="👌🏿 Да", callback_data=f"1_get_paypal:{wallet_name}"),
        InlineKeyboardButton(text="🤚🏿 Нет", callback_data="main_menu")
    )
    await bot.edit_message_text(
        chat_id=c.message.chat.id,
        message_id=c.message.message_id,
        text=f"🚀<b>ПАЛКА {wallet_name}</b>\n"
             f"<b>ВЫ БЕРЁТЕ НА СЕБЯ ЛИЧНО ВСЕ\nВОЗМОЖНЫЕ ПРЯМЫЕ\nИ КОСВЕННЫЕ РИСКИ!\n"
             f"ОБЯЗУЕТЕСЬ БЕЗ ПРЕТЕНЗИЙ!\n\n Подать запрос на палку?</b>",
        parse_mode="HTML",
        reply_markup=menu)


@dp.callback_query_handler(lambda c: c.data.startswith("1_get_paypal"))
async def on_pp(c: types.CallbackQuery):
    _type = c.data.split(':')[1]
    menu = InlineKeyboardMarkup(row_width=1)
    menu.add(
        InlineKeyboardButton(text="50-100€", callback_data=f"2_get_paypal:{_type}:50-100"),
        InlineKeyboardButton(text="100-250€", callback_data=f"2_get_paypal:{_type}:100-250"),
        InlineKeyboardButton(text="250€+", callback_data=f"2_get_paypal:{_type}:250+"),
        InlineKeyboardButton(text="Отмена ✋🏿", callback_data="main_menu")
    )
    await bot.edit_message_text(
        chat_id=c.message.chat.id,
        message_id=c.message.message_id,
        text="На какую сумму выдать палку?",
        reply_markup=menu)


@dp.callback_query_handler(lambda c: c.data.startswith("2_get_paypal"))
async def on_pp(c: types.CallbackQuery, state: FSMContext):
    _type = c.data.split(':')[1]
    _summ = c.data.split(':')[2]
    await bot.edit_message_text(
        chat_id=c.message.chat.id,
        message_id=c.message.message_id,
        text="🗂 <b>Отправьте 1 фото, где видно, что мамонт согласен оплатить</b>",
        parse_mode="HTML")
    await state.set_state(states.ReqPict.paypal)
    await state.update_data({"type": _type, "summ": _summ})


@dp.message_handler(content_types=['photo'], state=states.ReqPict.paypal)
async def on_pp(msg: types.Message, state: FSMContext):
    _data = await state.get_data()
    await state.finish()
    await bot.delete_message(
        chat_id=msg.chat.id,
        message_id=msg.message_id
    )
    await bot.send_message(
        msg.chat.id,
        "☑️ Запрос отправлен администратору!"
    )
    menu = InlineKeyboardMarkup()
    menu.row(
        InlineKeyboardButton(
            text="✅ Одобрить", callback_data=f"accept_pp_query:{msg.chat.id}:{_data['type']}:{_data['summ']}"
        ),
        InlineKeyboardButton(
            text="❌ Отклонить", callback_data=f"decline_pp_query:{msg.chat.id}"
        )
    )
    user = get_user(msg.chat.id)
    await bot.send_photo(
        config.admin_chat_id,
        msg.photo[-1].file_id,
        f"Заявка от пользователя {user[2]} (ID: {msg.chat.id})\n\nPayPal {_data['type']} {_data['summ']}",
        reply_markup=menu)


@dp.callback_query_handler(lambda c: c.data.startswith("accept_pp_query") and c.message.chat.id == config.admin_chat_id)
async def on_accept(c: types.CallbackQuery, state: FSMContext):
    _data = c.data.split(':')[1:]
    await bot.delete_message(chat_id=c.message.chat.id, message_id=c.message.message_id)
    await bot.send_message(c.message.chat.id, f"Отправьте информацию для заявки {_data[0]} {_data[1]} {_data[2]}")
    await state.set_state(states.AdminState.answer_query)
    await state.update_data({"info": _data})


@dp.message_handler(state=states.AdminState.answer_query, content_types=['text'])
async def on_as(msg: types.message, state: FSMContext):
    _data = (await state.get_data())['info']
    user = get_user(int(_data[0]))
    menu = InlineKeyboardMarkup()
    menu.add(InlineKeyboardButton(text="Отпустить ПП", callback_data=f"free_user:{_data[0]}"),
             InlineKeyboardButton(text="Залёт!", callback_data=f"profit_user:{_data[0]}"))
    await bot.send_message(
        chat_id=msg.chat.id,
        text=f"Информация по заявке ({user[2]} {_data[1]} {_data[2]}) была отправлена.",
        reply_markup=menu
    )
    await state.finish()
    await bot.send_message(
        _data[0],
        text=f"Ваша заявка по запросу {_data[1]} {_data[2]} была одобрена.\nПЕРЕВЕДИТЕ СРЕДСТВА НА УКАЗАННУЮ ПОЧТУ:\n\n{msg.text}"
    )
    _s = dp.current_state(chat=int(_data[0]))
    await _s.set_state(states.Holded.paypal)


@dp.callback_query_handler(lambda c: c.data.startswith("free_user"))
async def on_free(c: types.CallbackQuery):
    user_id = int(c.data.split(":")[1])
    await bot.edit_message_text(
        chat_id=c.message.chat.id,
        message_id=c.message.message_id,
        text="✔️ Заявка была отработана! (1/1)"
    )
    await bot.send_message(
        user_id,
        "Отпустил PayPal!"
    )
    _s = dp.current_state(chat=user_id)
    await _s.finish()


@dp.callback_query_handler(lambda c: c.data.startswith("profit_user"))
async def on_profit(c: types.CallbackQuery, state: FSMContext):
    user_id = int(c.data.split(':')[1])
    await bot.send_message(c.message.chat.id, "Укажите сумму профита в €")
    await bot.edit_message_text(
        chat_id=c.message.chat.id,
        message_id=c.message.message_id,
        text="✔️ Заявка была отработана! (1/2)"
    )
    await state.set_state(states.AdminState.summ)
    await state.update_data({"chat_id": user_id})


@dp.message_handler(content_types=['text'], state=states.AdminState.summ)
async def on_fu(msg: types.Message, state: FSMContext):
    if msg.chat.id != config.admin_chat_id:
        return
    if not msg.text.isdigit():
        if msg.text.find('.') != -1:
            if not msg.text.split('.')[0].isdigit() or not msg.text.split('.')[1].isdigit():
                await bot.send_message(msg.chat.id, "Некорректный формат")
                return
        elif msg.text.find(',') != -1:
            if not msg.text.split(',')[0].isdigit() or not msg.text.split(',')[1].isdigit():
                await bot.send_message(msg.chat.id, "Некорректный формат")
                return
        else:
            await bot.send_message(msg.chat.id, "Некорректный формат")
            return
    user_id = int((await state.get_data())["chat_id"])
    _paytag = get_user(user_id)[2]
    await state.finish()
    await bot.send_message(
        user_id,
        "Холд был снят. Поздравляем с залётом! 🎉",
        reply_markup=main_menu()
    )
    _s = dp.current_state(chat=user_id)
    await _s.finish()
    cursor.execute("insert into profits values (?, ?, ?)", (user_id, float(msg.text), datetime.date.today()))
    bdcon.commit()
    for i in config.notifications_chats:
        await bot.send_message(
            i, f"🎉 Вывели, GZ!!!🚀\n🧑🏿‍🦱 Воркер: {_paytag}\n💰 Сумма: {msg.text} €"
        )
    await bot.send_message(msg.chat.id, "Заявка была отработана (2/2) ✅")


@dp.callback_query_handler(lambda c: c.data == "get_iban")
async def on_iban(c: types.CallbackQuery, state: FSMContext):
    menu = InlineKeyboardMarkup()
    menu.row(
        InlineKeyboardButton(text="👌🏿 Да", callback_data=f"1_get_iban"),
        InlineKeyboardButton(text="🤚🏿 Нет", callback_data="main_menu")
    )
    await bot.edit_message_text(
        chat_id=c.message.chat.id,
        message_id=c.message.message_id,
        text=f"🚀<b>IBAN</b>\n"
             f"<b>ВЫ БЕРЁТЕ НА СЕБЯ ЛИЧНО ВСЕ\nВОЗМОЖНЫЕ ПРЯМЫЕ\nИ КОСВЕННЫЕ РИСКИ!\n"
             f"ОБЯЗУЕТЕСЬ БЕЗ ПРЕТЕНЗИЙ!\n\n Подать запрос на IBAN?</b>",
        parse_mode="HTML",
        reply_markup=menu)


@dp.callback_query_handler(lambda c: c.data == "1_get_iban")
async def on_iban(c: types.CallbackQuery, state: FSMContext):
    await bot.edit_message_text(
        chat_id=c.message.chat.id,
        message_id=c.message.message_id,
        text="Заявка отправлена администратору!"
    )
    user = get_user(c.message.chat.id)
    menu = InlineKeyboardMarkup()
    menu.row(
        InlineKeyboardButton(text="✅ Принять", callback_data=f"accept_iban:{c.message.chat.id}"),
        InlineKeyboardButton(text="❌ Отклонить", callback_data=f"decline_iban:{c.message.chat.id}")
    )
    await bot.send_message(
        config.admin_chat_id,
        f"Новая заявка от {user[2]}\n\nIBAN",
        reply_markup=menu
    )


@dp.callback_query_handler(lambda c: c.data.startswith("accept_iban") and c.message.chat.id == config.admin_chat_id)
async def on_ai(c: types.CallbackQuery, state: FSMContext):
    await bot.send_message(c.message.chat.id, "Укажите информацию для отправки воркеру!")
    await state.set_state(states.AdminState.answer_iban)
    user_id = int(c.data.split(':')[1])
    await state.update_data({"chat_id": user_id})


@dp.message_handler(content_types=['text'], state=states.AdminState.answer_iban)
async def on_info_iban(msg: types.Message, state: FSMContext):
    user_id = (await state.get_data())["chat_id"]
    menu = InlineKeyboardMarkup()
    menu.add(InlineKeyboardButton(text="💵 Деньги переведены", callback_data="iban_moneys_send"))
    await bot.send_message(
        user_id,
        "Ваша заявка по запросу IBAN была принята!\nСообщение от Администратора:\n\n"+msg.text,
        reply_markup=menu
    )
    await state.finish()
    _s = dp.current_state(chat=user_id)
    await _s.set_state(states.Holded.iban)
    await bot.send_message(msg.chat.id, "Отправлено!")


@dp.callback_query_handler(lambda c: c.data == "iban_moneys_send", state=states.Holded.iban)
async def on_sended(c: types.CallbackQuery, state: FSMContext):
    await bot.edit_message_text(
        chat_id=c.message.chat.id,
        message_id=c.message.message_id,
        text="Заявка отправлена администратору!"
    )
    await state.finish()
    user = get_user(c.message.chat.id)
    menu = InlineKeyboardMarkup()
    menu.add(InlineKeyboardButton(text="Залёт!", callback_data=f"profit_user:{c.message.chat.id}"))
    await bot.send_message(
        config.admin_chat_id, f"Пользователь {user[2]} подтвердил, что деньги были переведены на IBAN!",
        reply_markup=menu
    )


@dp.callback_query_handler(lambda c: c.data == "menu_profile")
async def on_p(c: types.CallbackQuery):
    user = get_user(c.message.chat.id)
    if c.message.from_user.username is not None:
        _username = c.message.chat.username
    else:
        _username = "юзернейм не установлен"
    print(c.message.as_json())
    await bot.edit_message_text(
        chat_id=c.message.chat.id,
        message_id=c.message.message_id,
        text=f"Вы: {_username}\n"
        f"Ваш процент: {user[3]}\n",
        parse_mode="HTML",
        reply_markup=profile_menu(c.message.chat.id)
    )


@dp.callback_query_handler(lambda c: c.data == "menu_manual")
async def on_p(c: types.CallbackQuery):
    await bot.send_message(
        c.message.chat.id,
        config.manual_text,
        parse_mode='HTML'
    )


@dp.callback_query_handler(lambda c: c.data == "menu_paypal")
async def on_p(c: types.CallbackQuery):
    await bot.edit_message_text(
        chat_id=c.message.chat.id,
        message_id=c.message.message_id,
        text=config.paypal_info,
        parse_mode="HTML",
        reply_markup=paypal_menu()
    )


@dp.callback_query_handler(lambda c: c.data == "menu_iban")
async def on_p(c: types.CallbackQuery):
    await bot.edit_message_text(
        chat_id=c.message.chat.id,
        message_id=c.message.message_id,
        text=config.iban_info,
        parse_mode="HTML",
        reply_markup=iban_menu()
    )


@dp.callback_query_handler(lambda c: c.data == "menu_mentors")
async def on_p(c: types.CallbackQuery):
    await bot.edit_message_text(
        chat_id=c.message.chat.id,
        message_id=c.message.message_id,
        text=config.mentor_info,
        parse_mode="HTML",
        reply_markup=mentor_menu()
    )


"""
@dp.callback_query_handler(lambda c: c.data == "menu_help")
async def on_p(c: types.CallbackQuery):
    await bot.send_message(
        c.message.chat.id,
        config.help_text,
        parse_mode="HTML"
    )
"""



@dp.callback_query_handler(lambda c: c.data == "menu_chats")
async def on_p(c: types.CallbackQuery):
    await bot.edit_message_text(
        chat_id=c.message.chat.id,
        message_id=c.message.message_id,
        text=config.chat_info,
        reply_markup=chat_link_menu(),
        parse_mode="HTML"
    )


@dp.callback_query_handler(lambda c: c.data == "main_menu")
async def on_m(c: types.CallbackQuery):
    await bot.edit_message_text(
        chat_id=c.message.chat.id,
        message_id=c.message.message_id,
        text="Главное меню",
        reply_markup=main_menu()
    )


async def start_bot():
    await asyncio.gather(
        dp.start_polling(bot, error_sleep=0)
    )


if __name__ == '__main__':
    asyncio.run(start_bot())
