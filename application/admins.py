from application import app
from flask import render_template, session, redirect, request, flash, escape
from functools import wraps
from helper_functions import *


@app.route('/admins/')
@validate_admin
def admins():

    url = 'https://www.nseindia.com/live_market/dynaContent/live_watch' \
          '/option_chain/optionKeys.jsp?segmentLink=17&instrument=OPTIDX&symbol=BANKNIFTY&date=24MAY2018'

    retrieve_option_chain_data(url)

    return render_template('/admins/index.html')

