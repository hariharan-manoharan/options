from application import app
from flask import render_template, session, redirect, request, flash, escape
from functools import wraps
from helper_functions import *
import sched, time
import urllib2
import json
import cookielib

s = sched.scheduler(time.time, time.sleep)


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

    for data in datas:
        if data['name'] == 'NIFTY BANK':
            bnf_ltp = data['lastPrice']
            bnf_change = data['change']
        if data['name'] == 'NIFTY 50':
            nf_ltp = data['lastPrice']
            nf_change = data['change']

    return render_template('/admins/index.html', bnfltp = bnf_ltp, nfltp = nf_ltp, bnfchange = bnf_change, nfchange= nf_change )



@app.route('/admins/schedule/', methods=['GET','POST'])
@validate_admin
def schedule_jobs():

    if request.method == 'POST':

        url = 'https://www.nseindia.com/live_market/dynaContent/live_watch' \
          '/option_chain/optionKeys.jsp?segmentLink=17&instrument=OPTIDX&symbol=BANKNIFTY&date='+request.form['expirydate']
        s.enter(10, 1, retrieve_option_chain_data, argument=(url,))
        s.run()
        flash("Job Scheduled successfully for Bank Nifty Expiry - "+request.form['expirydate'], 'success')
        return redirect("/admins/")
