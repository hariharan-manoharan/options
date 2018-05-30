## PACKAGE IMPORTS

from application import app  # bleh. circular imports. needed though...
import sqlite3  # for database stuff
from flask import g, session, escape, redirect  # flask g object...needed
from functools import wraps
import re
import os.path
import requests
import pandas as pd
from bs4 import BeautifulSoup
import sched, time
from nsetools import Nse
from pprint import pprint
from nsepy import *
import quandl
from decimal import Decimal

import win32com.client as win32
import shutil


DATABASE = 'test_database.db'  # database location
quandl.ApiConfig.api_key = "niyGuVbtysUyWvT8Rx6Q"
nse = Nse()
# make a db connection
def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db


# close connection on app teardown
@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()


# query the database
def query_db(query, args=(), one=False):
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv


# insert a value into the db
def execute_query_db(query, args=()):
    """ USED LIKE SO:
			insert_db('insert into entries (title, text) values (?, ?)',[request.form['title'], request.form['text']])
	"""
    db = get_db()
    db.execute(query, args)
    db.commit()



def validate_admin(func):
    """
		Validates admins. If not logged in, redirects to login.
		If a student, redirects to student page. Otherwise, nothing.
		I have no idea how most of this works, so don't touch anything.
		To use, put '@validate_admin' after app route definition.
	"""

    @wraps(func)
    def f(*args, **kwds):
        if not 'isAdmin' in session:
            return redirect("/")
        if session['isAdmin'] == 0:
            return redirect("/students/")
        return func(*args, **kwds)

    return f





def retrieve_old_option_chain_data(url):
    print(time.time())
    Base_Url = (url)


    page = requests.get(Base_Url)
    Status_Code = page.status_code
    page_content = page.content

    soup = BeautifulSoup(page_content, 'html.parser')
    ##print(soup.prettify())

    option_table_class = soup.find_all(class_='opttbldata')
    option_table_id = soup.find_all(id='octable')

    col_list = []


    for my_table in option_table_id:
        table_head = my_table.find('thead')
        try:
            rows = table_head.find_all('tr')
            for tr in rows:
                cols = tr.find_all('th')
                for th in cols:
                    col_head = th.text
                    col_head_encoded = col_head.encode('utf8')
                    col_list.append(col_head_encoded.replace(" ", ""))
        except:
            print 'no thead'


    col_list_fnl = [e for e in col_list if e not in ('CALLS', 'PUTS', 'Chart', '\xc2\xa0')]



    # print col_list_fnl

    option_table_id_2 = soup.find(id='octable')
    all_trs = option_table_id_2.find_all('tr')
    req_row = option_table_id_2.find_all('tr')

    new_table_call = pd.DataFrame(index=range(0, len(req_row) - 3), columns=col_list_fnl[0:11])
    new_table_put = pd.DataFrame(index=range(0, len(req_row) - 3), columns=col_list_fnl[10:])

    row_maker = 0

    for row_number, tr_nos in enumerate(req_row):

        if row_number <= 1 or row_number == len(req_row) - 1:
            continue
        # This ensure that we use only rows with values
        td_columns = tr_nos.find_all('td')

        # This removes the graphs columns
        select_cols = td_columns[1:12]
        cols_horizontal = range(0, len(select_cols))

        for nu, column in enumerate(select_cols):
            utf_string = column.get_text()
            utf_string = utf_string.strip('\n\r\t": ')
            tr = utf_string.encode('utf')
            new_table_call.ix[row_maker, [nu]] = tr

        row_maker += 1

    row_maker = 0

    for row_number, tr_nos in enumerate(req_row):

        if row_number <= 1 or row_number == len(req_row) - 1:
            continue
        # This ensure that we use only rows with values
        td_columns = tr_nos.find_all('td')

        # This removes the graphs columns
        select_cols = td_columns[11:22]
        cols_horizontal = range(0, len(select_cols))

        for nu, column in enumerate(select_cols):
            utf_string = column.get_text()
            utf_string = utf_string.strip('\n\r\t": ')
            tr = utf_string.encode('utf')
            new_table_put.ix[row_maker, [nu]] = tr

        row_maker += 1


    execute_query_db('DELETE FROM PREVIOUS_DAY_OI_DETAILS')
    insert_current_oi_details_table(new_table_call, 'INSERT INTO PREVIOUS_DAY_OI_DETAILS(STRIKE_PRICE, CALL_OI, CALL_LTP) SELECT StrikePrice, OI, LTP FROM tmp')
    execute_query_db('DELETE FROM CURRENT_DAY_OI_DETAILS')
    insert_current_oi_details_table(new_table_call, 'INSERT INTO CURRENT_DAY_OI_DETAILS(STRIKE_PRICE) SELECT StrikePrice FROM tmp')
    update_current_oi_details_table(new_table_put, 'UPDATE PREVIOUS_DAY_OI_DETAILS SET PUT_OI = (SELECT OI FROM tmp WHERE PREVIOUS_DAY_OI_DETAILS.STRIKE_PRICE = tmp.StrikePrice), PUT_LTP = (SELECT LTP FROM tmp WHERE PREVIOUS_DAY_OI_DETAILS.STRIKE_PRICE = tmp.StrikePrice)')

    print(time.time())

def insert_current_oi_details_table(new_table, query):
    db = get_db()
    new_table.to_sql('tmp', db, if_exists='replace')
    execute_query_db(query)


def update_current_oi_details_table(new_table, query):
    db = get_db()
    new_table.to_sql('tmp', db, if_exists='replace')
    execute_query_db(query)


def removeSplChars(data):
    return re.sub('[^A-Za-z0-9 ]+', '', str(data))


    # Base_Url = ('https://www.nseindia.com/live_market/dynaContent/live_watch/live_index_watch.htm')
    #
    # page = requests.get(Base_Url)
    # Status_Code = page.status_code
    # page_content = page.content
    #
    # soup = BeautifulSoup(page_content, 'html.parser')
    # ##print(soup.prettify())
    #
    # tr_all = soup.find_all('tr')
    #
    # col_list = []
    # bank_nifty_live_details = []
    #
    #
    # try:
    #     rowSize = len(tr_all)
    #     rowCounter = 0
    #     for tr in tr_all:
    #         rowCounter +=1
    #         if(rowCounter==1):
    #             cols = tr.find_all('th')
    #             for th in cols:
    #                 col_head = th.text
    #                 col_head_encoded = col_head.encode('utf8')
    #                 col_list.append(col_head_encoded)
    #         if (rowCounter == 14):
    #             cols = tr.find_all('td')
    #             for th in cols:
    #                 col_head = th.text
    #                 col_head_encoded = col_head.encode('utf8')
    #                 bank_nifty_live_details.append(col_head_encoded)
    # except:
    #     print 'no thead'
    #
    #
    # print col_list
    # print bank_nifty_live_details



def retrieve_current_option_chain_data(url):
    with app.app_context():
        print(time.time())
        Base_Url = (url)
        counter = + 1

        page = requests.get(Base_Url)
        Status_Code = page.status_code
        page_content = page.content

        soup = BeautifulSoup(page_content, 'html.parser')
        ##print(soup.prettify())

        option_table_class = soup.find_all(class_='opttbldata')
        option_table_id = soup.find_all(id='octable')

        col_list = []


        for my_table in option_table_id:
            table_head = my_table.find('thead')
            try:
                rows = table_head.find_all('tr')
                for tr in rows:
                    cols = tr.find_all('th')
                    for th in cols:
                        col_head = th.text
                        col_head_encoded = col_head.encode('utf8')
                        col_list.append(col_head_encoded.replace(" ", ""))
            except:
                print 'no thead'


        col_list_fnl = [e for e in col_list if e not in ('CALLS', 'PUTS', 'Chart', '\xc2\xa0')]



        # print col_list_fnl

        option_table_id_2 = soup.find(id='octable')
        all_trs = option_table_id_2.find_all('tr')
        req_row = option_table_id_2.find_all('tr')

        new_table_call = pd.DataFrame(index=range(0, len(req_row) - 3), columns=col_list_fnl[0:11])
        new_table_put = pd.DataFrame(index=range(0, len(req_row) - 3), columns=col_list_fnl[10:])

        row_maker = 0

        for row_number, tr_nos in enumerate(req_row):

            if row_number <= 1 or row_number == len(req_row) - 1:
                continue
            # This ensure that we use only rows with values
            td_columns = tr_nos.find_all('td')

            # This removes the graphs columns
            select_cols = td_columns[1:12]
            cols_horizontal = range(0, len(select_cols))

            for nu, column in enumerate(select_cols):
                utf_string = column.get_text()
                utf_string = utf_string.strip('\n\r\t": ')
                tr = utf_string.encode('utf')
                new_table_call.ix[row_maker, [nu]] = tr

            row_maker += 1

        row_maker = 0

        for row_number, tr_nos in enumerate(req_row):

            if row_number <= 1 or row_number == len(req_row) - 1:
                continue
            # This ensure that we use only rows with values
            td_columns = tr_nos.find_all('td')

            # This removes the graphs columns
            select_cols = td_columns[11:22]
            cols_horizontal = range(0, len(select_cols))

            for nu, column in enumerate(select_cols):
                utf_string = column.get_text()
                utf_string = utf_string.strip('\n\r\t": ')
                tr = utf_string.encode('utf')
                new_table_put.ix[row_maker, [nu]] = tr

            row_maker += 1


        update_current_oi_details_table(new_table_call,
                                        'UPDATE CURRENT_DAY_OI_DETAILS SET '
                                        'CALL_OI = (SELECT OI FROM tmp WHERE CURRENT_DAY_OI_DETAILS.STRIKE_PRICE = tmp.StrikePrice), '
                                        'CALL_CHANGE_IN_OI = (SELECT ChnginOI FROM tmp WHERE CURRENT_DAY_OI_DETAILS.STRIKE_PRICE = tmp.StrikePrice),'
                                        'CALL_LTP = (SELECT LTP FROM tmp WHERE CURRENT_DAY_OI_DETAILS.STRIKE_PRICE = tmp.StrikePrice)')
        update_current_oi_details_table(new_table_put,
                                        'UPDATE CURRENT_DAY_OI_DETAILS SET '
                                        'PUT_OI = (SELECT OI FROM tmp WHERE CURRENT_DAY_OI_DETAILS.STRIKE_PRICE = tmp.StrikePrice), '
                                        'PUT_CHANGE_IN_OI = (SELECT ChnginOI FROM tmp WHERE CURRENT_DAY_OI_DETAILS.STRIKE_PRICE = tmp.StrikePrice), '
                                        'PUT_LTP = (SELECT LTP FROM tmp WHERE CURRENT_DAY_OI_DETAILS.STRIKE_PRICE = tmp.StrikePrice)')
        print(time.time())


hist_oi_data = []


def get_call_oi_change_details():

    oiDatas = query_db('SELECT STRIKE_PRICE, CALL_LTP, CALL_OI, CALL_CHANGE_IN_OI FROM CURRENT_DAY_OI_DETAILS')


    OIDATAS = []

    for oidata in oiDatas:

        holderDict = {}
        if '-' not in oidata:
            holderDict['strikePrice'] = oidata[0].encode("utf-8")
            holderDict['callLtp'] = oidata[1].encode("utf-8")
            holderDict['callOi'] = oidata[2].encode("utf-8")
            holderDict['callOiChange'] = oidata[3].encode("utf-8")

            callOi = oidata[2].encode("utf-8").replace(",", "")
            callOiChange = oidata[3].encode("utf-8").replace(",", "")

            if callOiChange != callOi:
                denominator = (Decimal(callOi) - Decimal(callOiChange))
                prctChange = round(((Decimal(callOi)/denominator)-1)*100,2)
                holderDict['callOiChangePerct'] = prctChange
            else:
                holderDict['callOiChangePerct'] = '100'
            OIDATAS.append(holderDict)

    hist_oi_data.append(OIDATAS)

    return OIDATAS



def get_put_oi_change_details():

    oiDatas = query_db('SELECT STRIKE_PRICE, PUT_LTP, PUT_OI, PUT_CHANGE_IN_OI FROM CURRENT_DAY_OI_DETAILS')


    OIDATAS = []

    for oidata in oiDatas:

        holderDict = {}
        if '-' not in oidata:
            holderDict['strikePrice'] = oidata[0].encode("utf-8")
            holderDict['putLtp'] = oidata[1].encode("utf-8")
            holderDict['putOi'] = oidata[2].encode("utf-8")
            holderDict['putOiChange'] = oidata[3].encode("utf-8")


            putOi = oidata[2].encode("utf-8").replace(",", "")
            putOiChange = oidata[3].encode("utf-8").replace(",", "")

            if putOiChange != putOi:
                denominator = (Decimal(putOi) - Decimal(putOiChange))
                prctChange = round(((Decimal(putOi)/denominator)-1)*100,2)
                holderDict['putOiChangePerct'] = prctChange
            else:
                holderDict['putOiChangePerct'] = '100'


            OIDATAS.append(holderDict)

    return OIDATAS



def get_max_oi(query):
    datas = query_db(query)

    holderDict = {}
    for data in datas:
        if '-' not in data:
            holderDict['strikePrice'] = data[0].encode("utf-8")
            holderDict['maxOi'] = data[1].encode("utf-8")

    return holderDict


def calculate_pcr():

    total_call_oi = query_db("SELECT SUM(CAST(REPLACE(CALL_OI, ',', '') AS INT)) FROM CURRENT_DAY_OI_DETAILS")
    total_put_oi = query_db("SELECT SUM(CAST(REPLACE(PUT_OI, ',', '') AS INT)) FROM CURRENT_DAY_OI_DETAILS")


    holderDict = {}

    for data in total_call_oi:
        holderDict['total_call_oi'] = data[0]

    for data in total_put_oi:
        holderDict['total_put_oi'] = data[0]

    pcr = Decimal(holderDict['total_put_oi'])/Decimal(holderDict['total_call_oi'])

    return round(pcr,3)


def get_future_datatable_head():
    Base_Url = ('https://www.nseindia.com/live_market/dynaContent/live_watch/fomwatchsymbol.jsp?key=BANKNIFTY&Fut_Opt=Futures')

    page = requests.get(Base_Url)
    Status_Code = page.status_code
    page_content = page.content

    soup = BeautifulSoup(page_content, 'html.parser')

    col_list = []

    rows = soup.find_all('tr')

    try:
        for tr in rows:
            cols = tr.find_all('th')
            for th in cols:
                col_head = th.text
                col_head_encoded = col_head.encode('utf8')
                col_list.append(col_head_encoded.replace(" ", ""))
    except:
        print 'no thead'


    return col_list

def get_future_datatable_details():
    Base_Url = (
    'https://www.nseindia.com/live_market/dynaContent/live_watch/fomwatchsymbol.jsp?key=BANKNIFTY&Fut_Opt=Futures')

    page = requests.get(Base_Url)
    Status_Code = page.status_code
    page_content = page.content

    soup = BeautifulSoup(page_content, 'html.parser')


    rows = soup.find_all('tr')
    index_futures_list  = []
    counter = 0
    try:
        for tr in rows:
            counter += 1
            if counter <= 3:
                continue
            else:
                tds = tr.find_all('td')
                temp_list = []
                for td in tds:
                    td_text = td.text
                    td_text_encoded = td_text.encode('utf8')
                    temp_list.append(td_text_encoded.replace(" ", ""))
                index_futures_list.append(temp_list)
    except:
        print 'no td'

    return index_futures_list