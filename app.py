#Importing the Libraries
import numpy as np
import pandas as pd
from flask import Flask, request, render_template, redirect, url_for, session, logging, flash
from flask_cors import CORS
from flask_login import login_required, current_user, login_user, logout_user
from flask.logging import create_logger
from flask_mysqldb import MySQL
from functools import wraps
import MySQLdb.cursors
import re
import os
import joblib
import pickle
import flask
import secrets
from user_authentication import UserModel, loginManager, db
# from db_config import mysql
from werkzeug.security import generate_password_hash, check_password_hash
import newspaper
from newspaper import Article
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

        cursor = mysql.connection.cursor()
        cursor.execute('SELECT * FROM users WHERE email LIKE %s', (email,)) 
        account = cursor.fetchone()

        if account:
            password_db = account['password_hash']
            if check_password_hash(password_db,password):
                session['logged_in'] = True
                session['username'] = account['username']
                flash('You have successfully logged in!', 'success')
                return redirect(url_for('main'))
            else:
                msg = "Invalid Password"
                return render_template('login.html', msg=msg, email=email)

            cursor.close()
        else:
            flash('Account with this email address does not exist! Please try again!', 'danger')
     
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
            msg = "Email already exists!"
            return render_template('register.html', msg=msg, email=email, username=username)
        elif not re.match(r'[^@]+@[^@]+\.[^@]+', email): 
            msg = 'Invalid email address !'
            return render_template('register.html', msg=msg)
        elif not re.match(r'[A-Za-z0-9]+', username): 
            msg = 'Username must contain only characters and numbers !'
            return render_template('register.html', msg=msg)
        elif not username or not password or not email: 
            msg = 'Please fill out the form !'
            return render_template('register.html', msg=msg)
        else:     
            cursor.execute("INSERT INTO users(email, username, password_hash) VALUES(%s,%s,%s)", (email, username, password_hash))
            mysql.connection.commit()
            cursor.close()
            flash('You have successfully registered and you are allowed to login', 'success')
            return redirect(url_for('login'))
 
        # if UserModel.query.filter_by(email=email).first():
        #     # return ('Email already Present')
        #     return redirect(url_for('register'))
        # else:
        #     user = UserModel(email=email, username=username)
        #     user.set_password(password)
        #     db.session.add(user)
        #     db.session.commit()
        #     return redirect(url_for('login'))
             
        
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
# @login_required
def history():
    return render_template('history.html')

#Receiving the input url from the user and using Web Scrapping to extract the news content
@app.route('/predict',methods=['GET','POST'])
def predict():
    url = request.get_data(as_text=True)[5:]
    url = urllib.parse.unquote(url)

    if url:
        article = Article(str(url))
        article.download()
        article.parse()
        article.nlp()
        news_title = article.title
        news = article.text
        news_html = article.html
        
        #news = news_title + ' ' + news_text

        if article:
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
            
            # return render_template('predict.html', prediction_text='{}'.format(pred[0]), url_input=url)
            return render_template('predict.html', prediction_text=pred_outcome, url_input=url, news=news)
        else:
            flash('Invalid URL! Please try again', 'danger')
            return redirect(url_for('main'))
    else:
        flash('Please enter an URL to predict', 'danger')
        return redirect(url_for('main'))

    return render_template('predict.html')
    # return article.summary

if __name__=="__main__":
    port=int(os.environ.get('PORT',5000))
    app.run(port=port,debug=True,use_reloader=False)