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

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

import logging
logging.basicConfig()



@app.route('/admins/')
@validate_admin
def admins():
    hdr = {
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.3',
        'Accept-Encoding': 'none',
        'Accept-Language': 'en-US,en;q=0.8',
        'Connection': 'keep-alive'}
    req = urllib2.Request("https://www.nseindia.com/homepage/Indices1.json", headers=hdr)
    opener = urllib2.build_opener()
    f = opener.open(req)
    json1 = json.loads(f.read())


    datas = json1['data']
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
            trigger=IntervalTrigger(seconds=30))
        # Shut down the scheduler when exiting the app
        atexit.register(lambda: scheduler.shutdown())


        flash("Current day OI details for Bank Nifty Expiry - " + request.form['expirydate'] + ' will be collected every 15 mins ', 'success')
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

    head = get_future_datatable_head()
    details = get_future_datatable_details()

    return render_template("/admins/bnffutures.html", ftablehead=head, fexpires=details)

