import sqlite3
import os
import sys
import traceback
import logging


def connection_db(sqlite_insert_query: str, text_done: str, read: bool):
    try:
        sqlite_connection = sqlite3.connect('sqlite_python.db')
        cursor = sqlite_connection.cursor()
        logging.info("База данных подключена к SQLite")

        cursor.execute(sqlite_insert_query)
        if read:
            total_rows = cursor.fetchall()
        sqlite_connection.commit()
        logging.info(text_done)
        cursor.close()

    except sqlite3.Error as error:
        logging.info("Класс исключения: ", error.__class__)
        logging.info("Исключение", error.args)
        logging.info("Печать подробноcтей исключения SQLite: ")
        exc_type, exc_value, exc_tb = sys.exc_info()
        logging.info(traceback.format_exception(exc_type, exc_value, exc_tb))
    finally:
        if sqlite_connection:
            sqlite_connection.close()
            logging.info("Соединение с SQLite закрыто")
        if read:
            return total_rows


def create_db():
    sqlite_create_table_query = '''CREATE TABLE account (
                                    id_record INTEGER PRIMARY KEY AUTOINCREMENT,
                                    user_id INTEGER NOT NULL,
                                    date DATE NOT NULL,
                                    record_type text NOT NULL,
                                    category text NOT NULL,
                                    amount INTEGER NOT NULL);'''
    connection_db(sqlite_create_table_query, "Таблица SQLite создана", False)


def check_db():
    if os.path.exists('sqlite_python.db'):
        return
    create_db()


def update_db():
    try:
        os.remove('sqlite_python.db')
    except Exception as e:
        logging.info('Path is not a file')
    create_db()


def insert_table(user_id: int, record_type: str, category: str, amount: int):
    sqlite_insert_query = f"""INSERT INTO account
                          (user_id, date, record_type, category, amount)  
                          VALUES  ({user_id}, date('now'), "{record_type}", "{category}", {amount})"""

    connection_db(sqlite_insert_query, "Запись успешно вставлена в таблицу account", False)


def delete_table(id: int):
    sqlite_delete_query = f"""DELETE FROM account
                              WHERE id_record = {id};"""
    connection_db(sqlite_delete_query, "Запись успешно удалена из таблицы account", False)


def read_table(sqlite_select_query: str):
    return connection_db(sqlite_select_query, "Данные прочитаны", True)


def get_balance():
    sqlite_select_query = f"""SELECT user_id, SUM(amount) AS balance
                             FROM account"""
    results = read_table(sqlite_select_query)
    return results


def show_all_records(user_id: int, period: str):
    sqlite_select_query = f"""SELECT id_record, date, record_type, 
                              category, amount from account {create_where_part(period, user_id)}"""

    results = read_table(sqlite_select_query)
    dict_results = []
    for record in results:
        dict_result = {
            'id_record': record[0],
            'date': record[1],
            'record_type': record[2],
            'category': record[3],
            'amount': record[4]
        }
        dict_results.append(dict_result)
    return dict_results


def show_statistics(user_id: int, period: str):
    sqlite_select_query = f"""SELECT record_type, category,  SUM(amount) AS total_sum
                             FROM account {create_where_part(period, user_id)}"""

    sqlite_select_query += " GROUP BY record_type, category"
    results = read_table(sqlite_select_query)

    dict_results = []
    for record in results:
        dict_result = {
            'record_type': record[0],
            'category': record[1],
            'amount': record[2]
        }
        dict_results.append(dict_result)
    return dict_results


def create_where_part(period: str, user_id: int):
    where_part = f' WHERE user_id = {user_id}'
    if period == 'day':
        where_part += " AND date = date('now')"
    elif period == 'week':
        where_part += " AND date BETWEEN date('now', '-7 days') AND date('now')"
    elif period == 'month':
        where_part += " AND date BETWEEN date('now','start of month') AND date('now','start of month', '+1 month')"
    elif period == 'year':
        where_part += " AND date BETWEEN date('now','start of year') AND date('now','start of year', '+1 year')"
    return where_part

