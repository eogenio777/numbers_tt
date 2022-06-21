import httplib2
import json
import psycopg2
import requests
import datetime
import time
import logging

from logging import handlers
from psycopg2 import sql
from googleapiclient.discovery import build
from oauth2client.service_account import ServiceAccountCredentials


def get_service_sacc():
    """    Получение сервисного аккаунта для доступа.

    :return: сервисный аккаунт для доступа
    """
    creds_json = "credentials.json"
    scopes = ['https://www.googleapis.com/auth/spreadsheets']

    creds_service = ServiceAccountCredentials.from_json_keyfile_name(creds_json, scopes).authorize(httplib2.Http())
    return build('sheets', 'v4', http=creds_service)


def get_rows_from_sheet(sheet_id: str) -> {}:
    """    Получение данных из онлайн ресурса (google таблицы).

    :param sheet_id: id google таблицы
    :return: словарь с данными
    """
    service = get_service_sacc()
    sheet = service.spreadsheets()

    resp = sheet.values().batchGet(spreadsheetId=sheet_id, ranges="Лист1!A2:D1000").execute()
    return resp


def parse_list_of_rows(rate: float, llist: [[]]) -> [()]:
    """     Парсинг списка списков в список кортежей для дальнейшего
    удобного сравнения с полученным из базы данных.

    :param rate: курс, требуемый для расчета цены в рублях
    :param llist: список с исходными данными
    :return: кортеж с модифицированными данными (добавлена стоимость в рублях)
    """
    # удаляем пустые списки (если были удалены в таблице)
    llist = [x for x in llist if len(x) != 0]
    for lst in llist:
        # num
        lst[0] = int(lst[0])
        # orderNum
        lst[1] = int(lst[1])
        # costUSD
        lst[2] = float(lst[2])
        # shipmentDate
        lst[3] = datetime.datetime.strptime(lst[3], '%d.%m.%Y').date()
        # costRUB
        lst.append(lst[2] * rate)
    list_of_tuples = [tuple(x) for x in llist]
    return list_of_tuples


def get_rub_to_usd_rate() -> float:
    """     Получение курса доллара запросом с сайта ЦБ.

    :return: курс в качестве float параметра
    """
    data = requests.get('https://www.cbr-xml-daily.ru/daily_json.js').json()
    return data['Valute']['USD']['Value']


def compare_lists_of_tuples(tlist_from_db: [()], tlist_new: [()], logger) -> []:
    """     Сравнение двух списков данных.

    :param tlist_from_db: старый список кортежей (из базы данных)
    :param tlist_new: новый список кортежей (из google таблицы)
    :param logger: объект для логгирования
    :return: список (заполненный - если есть изменения),
     в котором первый элемент - флаг операции:
        0 - изменены ряды
        1 - добавлены ряды
        -1 - удалены ряды
     а дальнейшие элементы - это измененные данные.

     В случае если список пуст - разницы нет, значит база данных
      синхронизирована с google таблицей.
    """
    tlist_from_db.sort()
    tlist_new.sort()
    difference = []

    # удалено рядов
    deleted = set(tlist_from_db) - set(tlist_new)
    deleted_ids = [x[2] for x in deleted]
    deleted_ids.sort()
    logger.info(f'deleted: {deleted}')

    # добавлено рядов
    added = set(tlist_new) - set(tlist_from_db)
    added_ids = [x[2] for x in added]
    added_ids.sort()
    logger.info(f'added: {added}')

    # неизменных рядов
    still_there = set(tlist_from_db) & set(tlist_new)
    logger.info(f'still there (count): {len(still_there)}')

    # оба списка одинаковы
    if tlist_from_db == tlist_new:
        logger.info('lists are the same')
    # есть добавленные и удаленные
    elif len(deleted) != 0 and len(added) != 0 and deleted_ids == added_ids:
        difference.append(0)
        logger.info('rows were updated')
        for item in added:
            difference.append(item)
    elif len(deleted) != 0:
        difference.append(-1)
        logger.info('rows were deleted')
        for item in deleted:
            difference.append(item)
    elif len(added) != 0:
        difference.append(1)
        logger.info('rows were added')
        for item in added:
            difference.append(item)

    return difference


def update_or_insert_rate(old_rate, current_rate, cursor, logger) -> None:
    """     Обновление курса в БД.

    :param old_rate: старый курс (предположительно из БД)
    :param current_rate: текущий курс (предположительно переданный в функцию)
    :param cursor: курсор для взаимодейстия с БД
    :param logger: объект для логгирования
    """
    logger.info(f'rate has changed from {old_rate} to {current_rate}, reinserting')
    if old_rate == 0:
        cursor.execute('INSERT INTO ExchangeRateRUBUSD (rate) '
                       'VALUES (%s)',
                       [current_rate]
                       )
    else:
        cursor.execute("UPDATE ExchangeRateRUBUSD "
                       "SET rate = %s "
                       "WHERE id = 1",
                       [current_rate]
                       )

        logger.info(f'updated rows: {cursor.rowcount}')

    cursor.execute('UPDATE Orders '
                   'SET costRUB = costUSD * %s',
                   [current_rate])


def crud_orders(difference, cursor, logger) -> None:
    """     Вставка, изменение и удаление рядов в БД (таблица Orders).

    :param difference: список различий в БД с флагом операции
    :param cursor: курсор для взаимодействия с БД
    :param logger: объект для логгирования
    """
    logger.info('values in sheet have changed, updating db')
    if difference[0] == -1:
        for item in difference[1:]:
            cursor.execute('DELETE FROM Orders '
                           'WHERE orderNum = %s',
                           [item[1]])
    elif difference[0] == 1:
        # были добавлены ряды
        insert = sql.SQL('INSERT INTO Orders (num, orderNum, costUSD, shipmentDate, costRUB) VALUES {}').format(
            sql.SQL(',').join(map(sql.Literal, difference[1:]))
        )
        cursor.execute(insert)
    elif difference[0] == 0:
        # были изменены ряды
        for item in difference[1:]:
            cursor.execute('UPDATE Orders '
                           'SET costUSD = %s, shipmentDate = %s, costRUB = %s '
                           'WHERE orderNum = %s',
                           [item[2], item[3], item[4], item[1]])


def fill_or_refill_db(conn, cursor, logger, sheet_id) -> None:
    """     Изменение БД в зависимости от изменений google таблицы.

    :param sheet_id: id google таблицы для взаимодействия
    :param conn: соединение с БД
    :param cursor: курсор для взаимодействия с БД
    :param logger: объект для логгирования
    """
    conn.autocommit = True

    cursor.execute('SELECT * FROM Orders')
    records = cursor.fetchall()

    # проверить курс на данный момент
    cursor.execute('SELECT rate FROM ExchangeRateRUBUSD')
    bd_rate = cursor.fetchone()
    # если курс еще не в базе, ставим 0 (позже он перепишется)
    old_rate = 0 if bd_rate is None else bd_rate[0]
    current_rate = get_rub_to_usd_rate()

    rows_dict = get_rows_from_sheet(sheet_id)
    # получить список списков со значениями из таблицы
    values_lst_lst = rows_dict['valueRanges'][0]['values']
    # парсинг списка списков в список кортежей
    values = parse_list_of_rows(old_rate, values_lst_lst)

    # список кортежей с разницей между записями с флагами на добавление, удаление и изменение
    difference = compare_lists_of_tuples(records, values, logger)

    # заполнить таблицу в бд впервые
    if len(records) == 0:
        insert = sql.SQL('INSERT INTO Orders (num, orderNum, costUSD, shipmentDate, costRUB) VALUES {}').format(
            sql.SQL(',').join(map(sql.Literal, values))
        )
        cursor.execute(insert)
    elif old_rate != current_rate:  # если изменился курс
        update_or_insert_rate(old_rate, current_rate, cursor, logger)
    elif len(difference) != 0:  # добавились, изминились или удалились записи
        crud_orders(difference, cursor, logger)
    else:
        # если ничего не изменилось в google sheet, то ничего не изменилось в бд
        logger.info('everything is up to date')


def main():
    logging.basicConfig(
        format='[%(levelname)s] %(asctime)s, %(name)s, line %(lineno)s, %(message)s',
        level=logging.INFO,
        handlers=[
            logging.handlers.TimedRotatingFileHandler(filename="logs\\main.log",
                                                      backupCount=1,
                                                      when="W0"),
        ])
    logger = logging.getLogger('MainLogger')
    logger.addHandler(logging.StreamHandler())
    config_file_name = "config.json"
    try:
        with open(config_file_name, "r", encoding="utf-8") as read_file:
            config = json.load(read_file)
    except EnvironmentError as err:
        raise SystemExit(err)

    dbname = config["db"]["dbname"]
    user = config["db"]["user"]
    password = config["db"]["password"]
    host = config["db"]["host"]
    port = config["db"]["port"]
    sheet_id = config["sheet_api"]["sheet_id"]
    while True:
        conn = psycopg2.connect(
            dsn=f"postgres://{user}:{password}@{host}:{port}/{dbname}")
        cursor = conn.cursor()
        fill_or_refill_db(conn, cursor, logger, sheet_id)

        cursor.close()
        conn.close()
        time.sleep(5)


if __name__ == '__main__':
    main()
