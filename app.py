#Importing the Libraries
import numpy as np
import pandas as pd
from flask import Flask, request, render_template, redirect, url_for, session, logging, flash
from flask_cors import CORS
from flask_login import login_required, current_user, login_user, logout_user
from flask.logging import create_logger
from flask_mysqldb import MySQL
from functools import wraps
from textblob import TextBlob
# from urllib import 
import MySQLdb.cursors
import re
import os
import joblib
import pickle
import flask
import secrets
import validators
from user_authentication import UserModel, loginManager, db
# from db_config import mysql
from werkzeug.security import generate_password_hash, check_password_hash
import newspaper
from newspaper import Article, Config
# from urllib import request, urlopen, URLError, parse
import urllib
from newsapi import NewsApiClient 
newsapi=NewsApiClient(api_key='2aa3ac1960ca48b2a5260ebe34c37e96')

secret = secrets.token_urlsafe(32)


#Loading Flask and assigning the model variable
app = Flask(__name__)
CORS(app)
app=flask.Flask(__name__,template_folder='templates')
app.config['SECRET_KEY'] = secret
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'fakenewsapp_db'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'
# app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite3'
# app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:''@localhost/fakenewsapp_db'
# app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
log = create_logger(app)

mysql = MySQL(app)
#mysql.init_app(app)
# db.init_app(app)
loginManager.init_app(app)
loginManager.login_view = 'login'

# @app.before_first_request
# def create_table():
#     db.create_all()

@app.route('/', methods=['GET', 'POST'])
def main():
    data = newsapi.get_top_headlines(language='en',country="us", category='general', page_size=10)
    #data = newsapi.get_everything(q='politics', language='en', page_size=10)
    l1=[]
    l2=[]
    for i in data['articles']:
        l1.append(i['title'])
        l2.append(i['url'])

    return render_template('main.html', l1=l1, l2=l2)   

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/login', methods = ['POST'])
def login_post():
    msg = ''
    email = ''

    if current_user.is_authenticated:
        return redirect('/history')
     
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        # user = UserModel.query.filter_by(email = email).first()

        try: 
            cursor = mysql.connection.cursor()
            cursor.execute('SELECT * FROM users WHERE email LIKE %s', (email,)) 
            account = cursor.fetchone()

            if account:
                password_db = account['password_hash']
                if check_password_hash(password_db,password):
                    session['logged_in'] = True
                    session['username'] = account['username']
                    session['id'] = account['id']
                    flash('You have successfully logged in!', 'success')
                    return redirect(url_for('main'))
                else:
                    flash('Wrong password! Please try again!', 'danger')
                    return render_template('login.html', email=email)

                cursor.close()
            else:
                flash('Account with this email address does not exist! Please try again!', 'danger')
        except:
            flash('We are having trouble connecting to the database! Please try again later!', 'danger')

    return redirect(url_for('login'))


@app.route('/register', methods=['POST', 'GET'])
def register():
    msg = ''
    email = ''
    username = ''
     
    if request.method == 'POST':

        email = request.form.get('email')
        username = request.form.get('username')
        password = request.form.get('password')
        password_hash = generate_password_hash(password)

        cursor = mysql.connection.cursor()
        cursor.execute('SELECT * FROM users WHERE email LIKE %s', (email,)) 
        account = cursor.fetchone()

        if account:
            flash('Email already exists!', 'danger')
            return render_template('register.html', username=username)
        elif (len(password)<8): 
            flash('Please use a stronger password (*Password must have at least 8 characters)', 'danger')
            return render_template('register.html', email=email, username=username)
        elif not username or not password or not email: 
            flash('Please fill out the form to register!', 'danger')
            return render_template('register.html')
        else:     
            cursor.execute("INSERT INTO users(email, username, password_hash) VALUES(%s,%s,%s)", (email, username, password_hash))
            mysql.connection.commit()
            cursor.close()
            flash('You have successfully registered and you are allowed to login', 'success')
            return redirect(url_for('login'))
             
        
    return render_template('register.html', msg=msg)

# Check if user logged in
def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('Please login to gain access of this page', 'danger')
            return redirect(url_for('login'))
    return wrap

@app.route('/logout')
def logout():
    session.clear()
    logout_user()
    return redirect('/')

@app.route('/history', methods = ['GET', 'POST'])
@is_logged_in
def history():
    userID = session['id']

    cursor = mysql.connection.cursor()
    result = cursor.execute('SELECT * FROM history WHERE userID LIKE %s ORDER BY historyDate DESC', (userID,)) 
    history = cursor.fetchall()

    if history:
        record = True
        return render_template('history.html', history=history, record=record)
    else:
        msg = 'No History Found'
        return render_template('history.html', msg=msg, record=record)

    cursor.close()
    

#Receiving the input url from the user and using Web Scrapping to extract the news content
@app.route('/predict',methods=['GET','POST'])
def predict():
    url = request.get_data(as_text=True)[5:]
    url = urllib.parse.unquote(url)

    validate = validators.url(url)

    if validate == True:
        user_agent = request.headers.get('User-Agent')
        config = Config()
        config.browser_user_agent = user_agent

        try:
            article = Article(str(url))
            article.download()
            article.parse()
            parsed = article.text

            if parsed:
                
                b = TextBlob(parsed)
                lang = b.detect_language()

                if lang == "en":
                    article.nlp()
                    news_title = article.title
                    news = article.text
                    news_html = article.html

                    if news:
                        news_to_predict = pd.Series(np.array([news]))

                        cleaner = pickle.load(open('TfidfVectorizer-new.sav', 'rb'))
                        model = pickle.load(open('ClassifierModel-new.sav', 'rb'))

                        cleaned_text = cleaner.transform(news_to_predict)
                        pred = model.predict(cleaned_text)
                        pred_outcome = format(pred[0])
                        if (pred_outcome == "0"):
                            outcome = "True"
                        else:
                            if (pred_outcome == "REAL"):
                                outcome = "True"
                            else:
                                outcome = "False"

                        if 'logged_in' in session:
                            userID = session['id']
                            saveHistory(userID, url, outcome)
                        
                        return render_template('predict.html', prediction_text=outcome, url_input=url, news=news)
                    else:
                        flash('Invalid URL! Please try again', 'danger')
                        return redirect(url_for('main'))
                else:
                    language_error = "We currently do not support this language"
                    return render_template('predict.html', language_error=language_error, url_input=url)
            else:
                flash('Invalid news article! Please try again', 'danger')
                return redirect(url_for('main'))
        except newspaper.article.ArticleException:
            flash('We currently do not support this website! Please try again', 'danger')
            return redirect(url_for('main'))
        
    else:
        flash('Please enter a valid news stie URL', 'danger')
        return redirect(url_for('main'))

    return render_template('predict.html')

def saveHistory(userID, url, outcome):
    cursor = mysql.connection.cursor()
    cursor.execute("INSERT INTO history(historyURL, historyLabel, userID) VALUES(%s,%s,%s)", (url, outcome, userID))
    mysql.connection.commit()
    cursor.close()


if __name__=="__main__":
    port=int(os.environ.get('PORT',5000))
    app.run(port=port,debug=True,use_reloader=False)