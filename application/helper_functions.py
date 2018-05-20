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



DATABASE = 'test_database.db'  # database location


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
def insert_db(query, args=()):
    """ USED LIKE SO:
			insert_db('insert into entries (title, text) values (?, ?)',[request.form['title'], request.form['text']])
	"""
    db = get_db()
    db.execute(query, args)
    db.commit()


def update_db(query, args=()):

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




def retrieve_option_chain_data(url):
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

    # print(new_table)
    #new_table_call.to_csv('BNF_OPT_CHAIN_CALL.csv')
    #new_table_put.to_csv('BNF_OPT_CHAIN_PUT.csv')
    insert_current_oi_details_table(new_table_call, 'INSERT INTO PREVIOUS_DAY_OI_DETAILS(STRIKE_PRICE, CALL_OI, CALL_LTP) SELECT StrikePrice, OI, LTP FROM tmp')
    update_current_oi_details_table(new_table_put, 'UPDATE PREVIOUS_DAY_OI_DETAILS SET PUT_OI = (SELECT OI FROM tmp WHERE PREVIOUS_DAY_OI_DETAILS.STRIKE_PRICE = tmp.StrikePrice), PUT_LTP = (SELECT LTP FROM tmp WHERE PREVIOUS_DAY_OI_DETAILS.STRIKE_PRICE = tmp.StrikePrice)')


def insert_current_oi_details_table(new_table, query):
    db = get_db()
    new_table.to_sql('tmp', db, if_exists='replace')
    insert_db('DELETE FROM PREVIOUS_DAY_OI_DETAILS')
    insert_db(query)


def update_current_oi_details_table(new_table, query):
    db = get_db()
    new_table.to_sql('tmp', db, if_exists='replace')
    update_db(query)


def removeSplChars(data):
    return re.sub('[^A-Za-z0-9 ]+', '', str(data))



























