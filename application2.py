from flask import Flask, render_template, request, redirect, url_for
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import sqlite3
from database_setup2 import Base, Lifter, Stats
import itertools
import psycopg2
from flask import session as login_session
import random, string
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import flash, make_response
import requests
from apiclient import discovery
import httplib2
from oauth2client import client
from google.auth.transport import requests
from google.cloud import datastore
import google.oauth2.id_token
import pyrebase




app = Flask(__name__)

engine = create_engine('sqlite:///olytotalcatalog2.db', connect_args={'check_same_thread': False})

CLIENT_ID = json.loads(open('client_secret.json', 'r').read())['web']['client_id']

Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()





@app.route('/fbconnect', methods=['POST'])
def fbconnect():
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    access_token = request.data
    print "access token received %s " % access_token


    app_id = json.loads(open('fb_client_secrets.json', 'r').read())[
        'web']['app_id']
    app_secret = json.loads(
        open('fb_client_secrets.json', 'r').read())['web']['app_secret']
    url = 'https://graph.facebook.com/oauth/access_token?grant_type=fb_exchange_token&client_id=%s&client_secret=%s&fb_exchange_token=%s' % (
        app_id, app_secret, access_token)
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]


    # Use token to get user info from API
    userinfo_url = "https://graph.facebook.com/v2.8/me"
    '''
        Due to the formatting for the result from the server token exchange we have to
        split the token first on commas and select the first index which gives us the key : value
        for the server access token then we split it on colons to pull out the actual token value
        and replace the remaining quotes with nothing so that it can be used directly in the graph
        api calls
    '''
    token = result.split(',')[0].split(':')[1].replace('"', '')

    url = 'https://graph.facebook.com/v2.8/me?access_token=%s&fields=name,id,email' % token
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]
    # print "url sent for API access:%s"% url
    # print "API JSON result: %s" % result
    data = json.loads(result)
    login_session['provider'] = 'facebook'
    login_session['username'] = data["name"]
    login_session['email'] = data["email"]
    login_session['facebook_id'] = data["id"]

    # The token must be stored in the login_session in order to properly logout
    login_session['access_token'] = token

    # Get user picture
    url = 'https://graph.facebook.com/v2.8/me/picture?access_token=%s&redirect=0&height=200&width=200' % token
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]
    data = json.loads(result)

    login_session['picture'] = data["data"]["url"]

    # see if user exists
    user_id = getUserID(login_session['email'])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']

    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;border-radius: 150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '

    flash("Now logged in as %s" % login_session['username'])
    return output

@app.route('/fbdisconnect')
def fbdisconnect():
    facebook_id = login_session['facebook_id']
    # The access token must me included to successfully logout
    access_token = login_session['access_token']
    url = 'https://graph.facebook.com/%s/permissions?access_token=%s' % (facebook_id,access_token)
    h = httplib2.Http()
    result = h.request(url, 'DELETE')[1]
    return "you have been logged out"


@app.route('/login')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits) for x in range(32))
    login_session['state'] = state
    return render_template('login.html')
    #return "The current session state is %s" %login_session['state']

firebase_request_adapter = requests.Request()
@app.route('/')
@app.route('/lifters', methods = ['GET'])
def showAllLifters():
    all = session.query(Stats).all()
    return render_template('allLifters.html', all = all)

@app.route('/lifters/add', methods = ['POST', 'GET'])
def addLifter():
    if request.method == 'POST':
        newStats = Stats(lifter_id = request.form['name'],gender=request.form['gender'], weightclass=request.form['weightclass'], clean_jerk =request.form['clean_jerk'], snatch = request.form['snatch'], total = request.form['total'])
        session.add(newStats)
        session.commit()
    if request.method == 'POST':
        newLifter = Lifter(name = request.form['name'])
        session.add(newLifter)
        session.commit()
        return redirect(url_for('showAllLifters'))
    else:
        return render_template('addLifter.html')

@app.route('/lifter/<int:id>/', methods = ['GET'])
def showLifter(id):
    lifter = session.query(Stats).filter_by(id = id)
    return render_template('showLifter.html', lifter = lifter)

@app.route('/lifter<int:id>/delete', methods = ['POST', 'GET'])
def deleteLifter(id):
    lifterToDelete = session.query(Stats).filter_by(id = id).one()
    if request.method == 'POST':
        session.delete(lifterToDelete)
        session.commit()
        return redirect(url_for('showAllLifters', all = all))
    else:
        return render_template('deleteLifter.html', lifterToDelete = lifterToDelete)

@app.route('/lifter<int:id>/edit', methods = ['POST', 'GET'])
def editLifter(id):
    lifter = session.query(Stats).filter_by(id = id).one()
    if request.method == 'POST':
        if request.form['name']:
            lifter.lifter_id = request.form['name']
        if request.form['gender']:
            lifter.gender = request.form['gender']
        if request.form['weightclass']:
            lifter.weightclass = request.form['weightclass']
        if request.form['clean_jerk']:
            lifter.weightclass = request.form['clean_jerk']
        if request.form['snatch']:
            lifter.weightclass = request.form['snatch']
        if request.form['total']:
            lifter.weightclass = request.form['total']
            session.add(lifter)
            session.commit()
        return redirect(url_for('showAllLifters', all = all))
    else:
        return render_template('editLifter.html', id = id, lifter = lifter)
    #return "edit page %s" % lifter.lifter_id








if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=8000)
