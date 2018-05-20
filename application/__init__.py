from flask import Flask, url_for, request, render_template
app = Flask(__name__)

import application.helper_functions
import application.index
import application.admins
import application.login
