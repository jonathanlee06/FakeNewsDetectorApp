#Importing the Libraries
import numpy as np
import pandas as pd
from flask import Flask, request,render_template
from flask_cors import CORS
import os
import joblib
import pickle
import flask
import os
import newspaper
from newspaper import Article
import urllib

#Loading Flask and assigning the model variable
app = Flask(__name__)
CORS(app)
app=flask.Flask(__name__,template_folder='templates')
app.config['TEMPLATES_AUTO_RELOAD'] = True

# with open('model.pickle', 'rb') as handle:
# 	model = pickle.load(handle)
# model = load_model("trained.h5")

@app.route('/', methods=['GET', 'POST'])
def main():
    return render_template('main.html')   

#Receiving the input url from the user and using Web Scrapping to extract the news content
@app.route('/predict',methods=['GET','POST'])
def predict():
    url =request.get_data(as_text=True)[5:]
    url = urllib.parse.unquote(url)
    article = Article(str(url))
    article.download()
    article.parse()
    article.nlp()
    news = article.text

    news_to_predict = pd.Series(np.array([news]))

    cleaner = pickle.load(open('TfidfVectorizer.sav', 'rb'))
    model = pickle.load(open('ClassifierModel.sav', 'rb'))

    cleaned_text = cleaner.transform(news_to_predict)
    pred = model.predict(cleaned_text)
    pred_outcome = format(pred[0])
    if (pred_outcome == "0"):
        outcome = "True"
    else:
        outcome = "False"
    
    # return render_template('predict.html', prediction_text='{}'.format(pred[0]), url_input=url)
    return render_template('predict.html', prediction_text=outcome, url_input=url)
    # return article.summary

if __name__=="__main__":
    port=int(os.environ.get('PORT',5000))
    app.run(port=port,debug=True,use_reloader=False)