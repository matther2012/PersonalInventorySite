# Flask imports
from flask import Flask, render_template, session, redirect, url_for, escape, request

# Peewee
from peewee import *

# File manipulation
import sys
import os
import os.path

# Custom support files
import models
#import adLDAP

import flask.ext.whooshalchemy



# Other
#from datetime import date

# ~~~~~~~~~~~~~~~~ Start Execution ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

# Create Flask app
app = Flask(__name__)

# ~~~~~~~~~~~~~~~~ Create Functions ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

# LDAP http://www.python-ldap.org/doc/html/installing.html

# ~~~~~~~~~~~~~~~~ Startup Functions ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

def init(isDebug):
	app.debug = isDebug

	# Generate secret key for session
	app.secret_key = os.urandom(20)

# ~~~~~~~~~~~~~~~~ Page Render Functions ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

def renderMainPage():
	query = models.Device.select(models.Device.serialNumber,
								 models.Device.typeCategory,
								 models.Device.description,
								 models.Device.issues,
								 models.Device.state
				).order_by(models.Device.idNumber)
	types = models.getDeviceTypes()
	return render_template('index.html',
			name=escape(session['displayName']),
			query=query,
			types=types,
			logoutURL=url_for('logout')
		)

@app.route('/')
def index():
	# http://flask.pocoo.org/snippets/15/

	# If user logged in
	if 'username' in session:
		# Render main page
		return renderMainPage()

	# Force user to login
	return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
	# If form has been submitted
	if request.method == 'POST':
		try:
			if (app.debug == True or areCredentialsValid(
					request.form['username'],
					request.form['password']
					)):
				# Set username and displayName in session
				session['username'] = request.form['username']
				session['displayName'] = session['username']
		except Exception as e:
			return str(e)

		try:
			# Send user back to index page
			# (if username wasnt set, it will redirect back to login screen)
			return redirect(url_for('index'))
		except Exception as e:
			return str(e)

	# Was not a POST, which means index or some other source sent user to login
	return render_template('login.html')

@app.route('/logout')
def logout():
	session.pop('username', None)
	session.pop('displayName', None)
	return redirect(url_for('index'))

@app.route('/search', methods=['POST'])
def search():
	if request.method == 'POST':
		search = request.form['searchField']

	return redirect(url_for('search_results', search=search))



@app.route('/search_results/<search>')
def search_results(search):
	#query = models.Device.query.whoosh_search(search)

	query = models.Device.select(models.Device.serialNumber,
								 models.Device.typeCategory,
								 models.Device.description,
								 models.Device.issues,
								 models.Device.state
								 ).where(
								 (models.Device.serialNumber ** search) |
								 (models.Device.typeCategory ** search) |
								 (models.Device.description ** search) |
								 (models.Device.issues ** search) |
								 (models.Device.state ** search)
								 ).order_by(models.Device.serialNumber)

	types = models.getDeviceTypes()
	return render_template('searchResults.html',
			query=query,
			types=types,
			logoutURL=url_for('logout')
		)

# ~~~~~~~~~~~~~~~~ Start page ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

init(True)

if __name__ == '__main__':
	ctx = app.test_request_context()
	ctx.push()
	app.preprocess_request()
	port = int(os.getenv('PORT', 8080))
	host = os.getenv('IP', '0.0.0.0')
	app.run(port=port, host=host)

	models.db.connect()

	models.Device.create(
		idNumber = 3,
		serialNumber = 'LCDI-0111',
		typeCategory = 'Tablet',
		description = 'This is a phone This is a phone This is a phone This is a phone',
		issues = 'None of note',
		photo = 'IMG_002.jpg',
		state = 'operational'
	)

	models.db.close()
