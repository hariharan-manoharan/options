from application import app
from flask import render_template, session, redirect, request, flash, escape
from functools import wraps
from helper_functions import *
import sched, time
import urllib2
import json
import cookielib
import time
import atexit
from operator import is_not
from functools import partial
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
import math

import logging
logging.basicConfig()


@app.route('/admins/')
@validate_admin
def admins():
    datas = get_basic_details()

    bnf_ltp = ''
    bnf_change = ''
    nf_ltp = ''
    nf_change = ''
    vix_ltp = ''
    vix_change = ''

    for data in datas:
        if data['name'] == 'NIFTY BANK':
            bnf_ltp = data['lastPrice']
            bnf_change = data['change']
        if data['name'] == 'NIFTY 50':
            nf_ltp = data['lastPrice']
            nf_change = data['change']
        if data['name'] == 'INDIA VIX':
            vix_ltp = data['lastPrice']
            vix_change = data['change']

   # test()
    return render_template('/admins/index.html', bnfltp = bnf_ltp, nfltp = nf_ltp, bnfchange = bnf_change, nfchange= nf_change, vix=vix_ltp, vixchange = vix_change )



@app.route('/admins/schedule/', methods=['GET','POST'])
@validate_admin
def collect_old_oi_details():

    if request.method == 'POST':

        url = 'https://www.nseindia.com/live_market/dynaContent/live_watch' \
          '/option_chain/optionKeys.jsp?segmentLink=17&instrument=OPTIDX&symbol=BANKNIFTY&date='+request.form['expirydate']

        retrieve_old_option_chain_data(url)
        flash("Successfully collected previous day OI details for Bank Nifty Expiry - "+request.form['expirydate'], 'success')
        return redirect("/admins/")


scheduler = BackgroundScheduler()

@app.route('/admins/collectoidetails/', methods=['GET','POST'])
@validate_admin
def collect_current_oi_details():

    if request.method == 'POST':
        url = 'https://www.nseindia.com/live_market/dynaContent/live_watch' \
              '/option_chain/optionKeys.jsp?segmentLink=17&instrument=OPTIDX&symbol=BANKNIFTY&date=' + request.form['expirydate']


        scheduler.start()
        scheduler.add_job(
            id='job1',
            func=retrieve_current_option_chain_data,
            args=[url],
            trigger=IntervalTrigger(minutes=1))
        # Shut down the scheduler when exiting the app
        atexit.register(lambda: scheduler.shutdown())


        flash("Current day OI details for Bank Nifty Expiry - " + request.form['expirydate'] + ' will be collected every 5 mins ', 'success')
        return redirect("/admins/")


@app.route('/admins/pausecollectoidetails/', methods=['GET','POST'])
@validate_admin
def pause_collect_current_oi_details():

    if request.method == 'POST':

        scheduler.pause()

        flash('Paused collecting current day OI details for Bank Nifty', 'success')
        return redirect("/admins/")

@app.route('/admins/resumecollectoidetails/', methods=['GET','POST'])
@validate_admin
def resume_collect_current_oi_details():

    if request.method == 'POST':

        scheduler.resume()

        flash('Resumed collecting current day OI details for Bank Nifty', 'success')
        return redirect("/admins/")

@app.route('/admins/calloichange/', methods=['GET'])
@validate_admin
def show_call_oi_details():

    if request.method == 'GET':

        call_datas = get_call_oi_change_details()

        max_call_oi = get_max_oi("SELECT STRIKE_PRICE, CALL_OI FROM CURRENT_DAY_OI_DETAILS WHERE CAST(REPLACE(CALL_OI, ',', '') AS INT) = (SELECT MAX(CAST(REPLACE(CALL_OI, ',', '') AS INT)) FROM CURRENT_DAY_OI_DETAILS)")

        pcr = calculate_pcr()

        return render_template("/admins/calloichange.html", calloidatas = call_datas, max_oi = max_call_oi, pcr = pcr)

@app.route('/admins/putoichange/', methods=['GET'])
@validate_admin
def show_put_oi_details():

    if request.method == 'GET':

        put_datas = get_put_oi_change_details()

        max_put_oi = get_max_oi("SELECT STRIKE_PRICE, PUT_OI FROM CURRENT_DAY_OI_DETAILS WHERE CAST(REPLACE(PUT_OI, ',', '') AS INT) = (SELECT MAX(CAST(REPLACE(PUT_OI, ',', '') AS INT)) FROM CURRENT_DAY_OI_DETAILS)")

        pcr = calculate_pcr()

        return render_template("/admins/putoichange.html",  putoidatas= put_datas, max_oi = max_put_oi,  pcr = pcr)


@app.route('/admins/bnffutures/', methods=['GET'])
@validate_admin
def show_futures_details():

    oiDatas = query_db('SELECT * FROM CALL_OI_TRACK')

    OIDATAS = []

    for i in range(0,len(oiDatas)):
        holderDict = []
        if '-' not in oiDatas[i]:
            holderDict.append(oiDatas[i])

    head = get_future_datatable_head()
    details = get_future_datatable_details()

    return render_template("/admins/bnffutures.html", ftablehead=head, fexpires=details)


@app.route('/admins/calloichart/', methods=['GET'])
@validate_admin
def show_call_oichart():
    datas = get_basic_details()

    bnf_ltp = 0.00

    for data in datas:
        if data['name'] == 'NIFTY BANK':
            bnf_ltp = Decimal(data['lastPrice'].encode("utf-8").replace(",", ""))
            break

    bnf_ltp = math.ceil(bnf_ltp/100)* 100

    count_in_db = query_db('SELECT MAX(JOB_SCHEDULE_COUNT) AS COUNT FROM OTHERS')
    datas = query_db('SELECT * FROM CALL_OI_TRACK')

    final_data_list = []

    for data in datas:
        filtered_datas = filter(partial(is_not, None), data)
        filtered_datas = [x.encode('utf-8').encode("utf-8").replace(",", "") for x in filtered_datas]
        final_data_list.append(filtered_datas)


    count = 0
    for c in count_in_db:
        count = c[0]

    f_list = []

    for data_list in final_data_list:
        new_list = []
        new_list.append(data_list[0])
        new_list.append(data_list[1:count+1])
        new_list.append(data_list[count+1 :count+count+1])
        new_list.append(data_list[count + count + 1 : count + count + count + 1])
        f_list.append(new_list)

    return render_template("/admins/calloichart.html" ,datas = f_list, count =count, bnf_ltp = bnf_ltp)



@app.route('/admins/putoichart/', methods=['GET'])
@validate_admin
def show_put_oichart():
    datas = get_basic_details()

    bnf_ltp = 0.00

    for data in datas:
        if data['name'] == 'NIFTY BANK':
            bnf_ltp = Decimal(data['lastPrice'].encode("utf-8").replace(",", ""))
            break

    bnf_ltp = math.ceil(bnf_ltp/100)* 100

    count_in_db = query_db('SELECT MAX(JOB_SCHEDULE_COUNT) AS COUNT FROM OTHERS')
    datas = query_db('SELECT * FROM PUT_OI_TRACK')

    final_data_list = []

    for data in datas:
        filtered_datas = filter(partial(is_not, None), data)
        filtered_datas = [x.encode('utf-8').encode("utf-8").replace(",", "") for x in filtered_datas]
        final_data_list.append(filtered_datas)


    count = 0
    for c in count_in_db:
        count = c[0]

    f_list = []

    for data_list in final_data_list:
        new_list = []
        new_list.append(data_list[0])
        new_list.append(data_list[1:count+1])
        new_list.append(data_list[count+1 :count+count+1])
        new_list.append(data_list[count + count + 1: count + count + count + 1])
        f_list.append(new_list)



    return render_template("/admins/putoichart.html" ,datas = f_list, count =count, bnf_ltp = bnf_ltp)

