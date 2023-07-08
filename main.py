import logging
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ApplicationBuilder, CallbackContext, CommandHandler, MessageHandler, filters, CallbackQueryHandler

import sqlite_m
from information_data import TOKEN_BOT, category_spending

users_balance = {}


def create_keyboard():
    keyboard = ReplyKeyboardMarkup(keyboard=[['Список категорий'], ['Записи расходов и доходов'],
                                              ['Статистика расходов и доходов']], resize_keyboard=True)
    return keyboard


def create_dict_periods(button):
    return {f'{button}|all': 'Все данные',
            f'{button}|day': 'День',
            f'{button}|week': 'Неделя',
            f'{button}|month': 'Месяц',
            f'{button}|year': 'Год',
            }


async def add_expense(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    adds_parts = " ".join(context.args).split("|")
    if len(adds_parts) == 2:
        if not adds_parts[0] in category_spending:
            categoryes = "{}".format('\n'.join(category_spending))
            await update.message.reply_text("Неправильная категория! Категории на расход могут быть только из следующего списка:\n" +
                                            categoryes)
            return
        elif users_balance[user_id] - int(adds_parts[1]) < 0:
            await update.message.reply_text("Нельзя добавить расход! Будет минусовый баланс")
            return
        sqlite_m.insert_table(user_id, "Расход", adds_parts[0], -int(adds_parts[1]))
        await update.message.reply_text(f"Record was successfully added!")
        update_users_balance()
    else:
        await update.message.reply_text(f"Record invalid format!")


async def add_income(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    adds_parts = " ".join(context.args).split("|")
    if len(adds_parts) == 2:
        sqlite_m.insert_table(user_id, "Приход", adds_parts[0], int(adds_parts[1]))
        await update.message.reply_text(f"Record was successfully added!")
        update_users_balance()
    else:
        await update.message.reply_text(f"Record invalid format!")


async def start(update: Update, context: CallbackContext) -> None:
    logging.info('Command "start" was triggered!')
    await update.message.reply_text(
        "Welcome to my Bot!\n"
        "Commands: \n"
        "Adding income: /income <category>|<amount>\n"
        "Adding expense: /expense <category>|<amount>\n"
        "Clean database: /clean_db\n"
        , reply_markup=create_keyboard())


async def handle_message(update: Update, context: CallbackContext) -> None:
    message_text = update.message.text
    match message_text:
        case 'Список категорий':
            await update.message.reply_text("Категории:\n{}".format('\n'.join(category_spending)))
        case 'Записи расходов и доходов':
            dict_periods = create_dict_periods('records')
            inline_keyboard = InlineKeyboardMarkup([[InlineKeyboardButton(value, callback_data=key)]
                                                    for key, value in dict_periods.items()])
            await update.message.reply_text(message_text, reply_markup=inline_keyboard)
        case 'Статистика расходов и доходов':
            dict_periods = create_dict_periods('statistics')
            inline_keyboard = InlineKeyboardMarkup([[InlineKeyboardButton(value, callback_data=key)]
                                                    for key, value in dict_periods.items()])
            await update.message.reply_text(message_text, reply_markup=inline_keyboard)
        case _:
            await update.message.reply_text(f"Введен текст: {message_text}")


async def handle_callback_query(update: Update, context: CallbackContext) -> None:
    user_id = update.callback_query.from_user.id
    query_parts = update.callback_query.data.split("|")
    if len(query_parts):
        if query_parts[0] == 'records':
            dict_results = sqlite_m.show_all_records(user_id, query_parts[1])
            await context.bot.send_message(user_id, f'Записи расходов и доходов ({query_parts[1]})')
            for dict_result in dict_results:
                await context.bot.send_message(update.callback_query.from_user.id, '\n'.join([key + ': ' + str(value) for key, value in dict_result.items()]),
                                               reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('Удалить',
                                                                                 callback_data=f'del|{dict_result["id_record"]}_{dict_result["amount"]}')]]))
        elif query_parts[0] == 'statistics':
            dict_results = sqlite_m.show_statistics(user_id, query_parts[1])
            new_msg = await context.bot.send_message(user_id, f'Статистика расходов и доходов ({query_parts[1]})')
            text_answer = ''
            for dict_result in dict_results:
                text_answer += '\n'.join([key + ': ' + str(value) for key, value in dict_result.items()])
                text_answer += '\n\n'
            text_answer += f'Текущий баланс: {users_balance[user_id]}'
            await new_msg.reply_text(text_answer)
        elif query_parts[0] == 'del':
            query_parts_del = query_parts[1].split("_")
            if users_balance[user_id] - int(query_parts_del[1]) < 0:
                await context.bot.answer_callback_query(callback_query_id=update.callback_query.id,
                                                        text="Нельзя удалить запись! Будет минусовый баланс", show_alert=True)
                return
            sqlite_m.delete_table(int(query_parts_del[0]))
            await context.bot.answer_callback_query(callback_query_id=update.callback_query.id, text="запись удалена", show_alert=False)
            await update.callback_query.message.delete()
            update_users_balance()
        else:
            await update.message.reply_text(f"invalid callback query {update.callback_query.data}!")
    else:
        await update.message.reply_text(f"invalid callback query {update.callback_query.data}!")


def update_users_balance():
    global users_balance
    users_balance = {key: int(value) for key, value in sqlite_m.get_balance() if not (value is None)}


def run():
    sqlite_m.check_db()
    update_users_balance()
    app = ApplicationBuilder().token(TOKEN_BOT).build()
    logging.info("Application built successfully!")

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", start))
    app.add_handler(CommandHandler("clean_db", sqlite_m.update_db))
    app.add_handler(CommandHandler("income", add_income))
    app.add_handler(CommandHandler("expense", add_expense))
    app.add_handler(MessageHandler(filters.TEXT, handle_message))
    app.add_handler(CallbackQueryHandler(handle_callback_query))
    app.run_polling()


if __name__ == '__main__':
    run()
