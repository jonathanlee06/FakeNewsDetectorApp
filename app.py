#Importing the Libraries
import numpy as np
import pandas as pd
from flask import Flask, request, render_template, redirect, url_for, Blueprint
from flask_cors import CORS
from flask_login import login_required, current_user, login_user, logout_user
from flask.logging import create_logger
import os
import joblib
import pickle
import flask
import secrets
from user_authentication import UserModel, loginManager, db
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
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite3'
# app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
log = create_logger(app)

db.init_app(app)
loginManager.init_app(app)
loginManager.login_view = 'login'

@app.before_first_request
def create_table():
    db.create_all()

@app.route('/', methods=['GET', 'POST'])
def main():
    data = newsapi.get_top_headlines(language='en',country="my", page_size=10)
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
    if current_user.is_authenticated:
        return redirect('/history')
     
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = UserModel.query.filter_by(email = email).first()

        if not user and not user.check_password(user.password, password):
            return redirect(url_for('login'))
            # return redirect(url_for('history')) 
       
        login_user(user)
        print("Email is here " + email) 
     
    return redirect(url_for('history'))

@app.route('/register', methods=['POST', 'GET'])
def register():
    if current_user.is_authenticated:
        return redirect('/history')
     
    if request.method == 'POST':

        # email = request.form['email']
        # username = request.form['username']
        # password = request.form['password']

        email = request.form.get('email')
        username = request.form.get('username')
        password = request.form.get('password')
 
        if UserModel.query.filter_by(email=email).first():
            # return ('Email already Present')
            return redirect(url_for('register'))
        else:
            user = UserModel(email=email, username=username)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            return redirect(url_for('login'))
             
        
    return render_template('register.html')

@app.route('/logout')
def logout():
    logout_user()
    return redirect('/')

@app.route('/history', methods = ['GET', 'POST'])
@login_required
def history():
    return render_template('history.html')

#Receiving the input url from the user and using Web Scrapping to extract the news content
@app.route('/predict',methods=['GET','POST'])
def predict():
    url = request.get_data(as_text=True)[5:]
    url = urllib.parse.unquote(url)
    article = Article(str(url))
    article.download()
    article.parse()
    article.nlp()
    news_title = article.title
    news = article.text
    #news = news_title + ' ' + news_text

    news_to_predict = pd.Series(np.array([news]))

    cleaner = pickle.load(open('TfidfVectorizer.sav', 'rb'))
    model = pickle.load(open('ClassifierModel.sav', 'rb'))

    cleaned_text = cleaner.transform(news_to_predict)
    pred = model.predict(cleaned_text)
    pred_outcome = format(pred[0])
    if (pred_outcome == "0"):
        outcome = "True"
    else:
        if (pred_outcome == "Valid"):
            outcome = "True"
        else:
            outcome = "False"
    
    # return render_template('predict.html', prediction_text='{}'.format(pred[0]), url_input=url)
    return render_template('predict.html', prediction_text=outcome, url_input=url, news=news)
    # return article.summary

if __name__=="__main__":
    port=int(os.environ.get('PORT',5000))
    app.run(port=port,debug=True,use_reloader=False)