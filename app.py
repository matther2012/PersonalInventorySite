# Flask imports
from flask import Flask, render_template, session, redirect, url_for, escape, request, jsonify
from werkzeug import secure_filename
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

UPLOAD_FOLDER = 'static/item_photos'
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif', 'PNG', 'JPG', 'JPEG', 'GIF'])


# Other
#from datetime import date

# ~~~~~~~~~~~~~~~~ Start Execution ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

# Create Flask app
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
# ~~~~~~~~~~~~~~~~ Create Functions ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

# LDAP http://www.python-ldap.org/doc/html/installing.html

# ~~~~~~~~~~~~~~~~ Startup Functions ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

def init(isDebug):
	app.debug = isDebug

	# Generate secret key for session
	app.secret_key = os.urandom(20)

# ~~~~~~~~~~~~~~~~ Page Render Functions ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

def renderMainPage():
	query = models.Device.select().order_by(models.Device.serialNumber)
	types = models.getDeviceTypes()
	states = models.getStates()
	return render_template('index.html',
			name=escape(session['displayName']),
			query=query,
			types=types,
			states=states,
			totalItems=len(query),
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
	if search != "":
		return redirect(url_for('search_results', search=search))
	else:
		return redirect(url_for('index'))



@app.route('/search_results/<search>')
def search_results(search):
	#query = models.Device.query.whoosh_search(search)

	query = models.Device.select(models.Device.serialNumber,
								 models.Device.typeCategory,
								 models.Device.description,
								 models.Device.issues,
								 models.Device.state
								 ).where(models.Device.serialNumber.contains(search) | 
								 		 models.Device.typeCategory.contains(search) |
								 		 models.Device.description.contains(search)).order_by(models.Device.serialNumber)

	types = models.getDeviceTypes()
	return render_template('searchResults.html',
			query=query,
			types=types,
			logoutURL=url_for('logout')
		)
		
@app.route('/viewItem/<serial>')
def viewItem(serial):
	item = models.Device.select().where(models.Device.serialNumber == serial)
	types = models.getDeviceTypes()
	states = models.getStates()
	return render_template('viewItem.html',
			item=item,
			types=types,
			states=states,
			logoutURL=url_for('logout')
		)
		
@app.route('/', methods=['POST'])
def addItem():
	if request.method == 'POST':
		
		idNum = models.Device.select().order_by(models.Device.idNumber.desc()).get()
		
		if request.form['device_types'] == 'Other':
			device_type = request.form['other']
		else:
			device_type = request.form['device_types']
			
		file = request.files['file']
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
			
	models.Device.create(
			idNumber = idNum.idNumber + 1,
			serialNumber = request.form['lcdi_serial'],
			typeCategory = device_type,
			description = request.form['device_desc'],
			issues = request.form['device_notes'],
			photo = file.filename,
			state = request.form['device_state']
		)
		
	return redirect(url_for('viewItem', serial=request.form['lcdi_serial']))
	
@app.route('/deleteItem/<serial>')
def deleteItem(serial):
	
	item = models.Device.select().where(models.Device.serialNumber == serial).get();
	item.delete_instance();
	return redirect(url_for('index'))
	
@app.route('/updateItem/<serial>', methods=['POST'])
def updateItem(serial):
	
	if request.method == 'POST':
		
		item = models.Device.select().where(models.Device.serialNumber == serial).get()
		
		if request.form['device_types'] == 'Other':
			device_type = request.form['other']
		else:
			device_type = request.form['device_types']
			
			
		file = request.files['file']
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
			
			
	item.serialNumber = request.form['lcdi_serial']
	item.typeCategory = device_type
	item.description = request.form['device_desc']
	item.issues = request.form['device_notes']
	if file:
		item.photo = file.filename
	item.state = request.form['device_state']
	
	item.save()
	
	return redirect(url_for('viewItem', serial=item.serialNumber))
	

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS


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
	
	"""models.Device.create_table()
	models.InOut.create_table()"""
	
	models.Device.create(
		idNumber = 2,
		serialNumber = 'LCDI-1111',
		typeCategory = 'Phone',
		description = 'iPhone 6 Plus',
		issues = 'None of note',
		photo = 'IMG_001.png',
		state = 'Operational'
	)
	
	models.InOut.create(
		idNumber = 2,
		studentName = 'Matthew Fortier',
		use = 'iOS Forensics',
		userIn = 'N/A',
		userOut = 'mfortier',
		issues = 'None of note'
	)
	

	models.db.close()
