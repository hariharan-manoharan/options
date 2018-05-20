##IMPORTS

from application import app #circular import because its needed for modular code. I know its ugly. Shhh.
from flask import request, render_template, redirect, flash, session #imports for various flask functions
from os import urandom #generating salt
import hashlib #library for hashing (fairly self-explanatory :P)
from helper_functions import *

###LOGIN THE USER
@app.route('/login/', methods=['POST'])
def login():
	# get form information
	formData = request.form
	
	# validation
	if formData['username'] == "":
		flash("The username field is required.")
		return redirect("/")
	if formData['password'] == "":
		flash("The password field is required.")
		return redirect("/")

	#get data from database
	data = query_db("SELECT PASSWORD, SALT, ISADMIN, USERID FROM USERS WHERE USERNAME=? LIMIT 1", [formData['username']])
	#print data
	#make sure username is right
	if data == []:
		flash("Your username was incorrect.")
		return redirect("/")

	# check the password	
	if data[0][0] == hashlib.md5(data[0][1] + formData['password']).hexdigest():
		#correct password
		session['isAdmin'] = data[0][2]
		session['id'] = data[0][3]
		#if student, redirect to students page
		if session['isAdmin'] == 0:
			return redirect("/students/")
		#else they are a admin, redirect to admins page
		else:
			session['isAdmin'] = True
			return redirect("/admins/")

	flash("Your password was incorrect.")
	return redirect("/")

###REGISTER THE USER
@app.route('/register/', methods=['GET', 'POST'])
def register():
	
	#form data is GET, so render template
	if request.method == 'GET':
		return render_template('register.html')

	#request method is POST, so do everything
	
	formData = request.form
	
	#form validation
	if formData['username'] == "" or formData['password'] == "" or formData['name'] == "" or formData['email'] == "":
		return "All text fields are required"
	if not 'isAdmin' in formData: #if is admin wasn't selected
		isAdmin = 0 #they aren't a admin...
	else:
		isAdmin = 1 #they are a admin!
	
	#hash w/salt
	salt = urandom(16).encode("hex")
	password = hashlib.md5(salt + formData['password']).hexdigest()
	insert_db("INSERT INTO USERS (USERNAME,PASSWORD,SALT,ISADMIN,NAME,EMAIL) VALUES (?, ?, ?, ?, ?, ?)", [formData['username'], password, salt, isAdmin, formData['name'], formData['email']])
	flash("The entry was created")
	return redirect("/register/")
