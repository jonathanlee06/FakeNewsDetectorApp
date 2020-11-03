import numpy as np 
import pandas as pd 
import pickle
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import PassiveAggressiveClassifier
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from sklearn.model_selection import cross_val_score
import matplotlib.pyplot as plt
import scikitplot.plotters as skplt
import warnings

warnings.filterwarnings('ignore')

def plot_cmat(yte, ypred):
    '''Plotting confusion matrix'''
    skplt.plot_confusion_matrix(yte,ypred)
    plt.show()

# Import dataset for training using Pandas
news = pd.read_csv('datasets/train.csv')
text = news['text'].astype('U')
label = news['label'].astype('U')

# Splitting the dataset into test and train
text_train, text_test, label_train, label_test = train_test_split(text, label, test_size=0.2, random_state=5)

# Insert spliitted data into TfidfVectorizer and transform shape
vectorizer = TfidfVectorizer(stop_words='english', max_df=0.7)

transformed_text_train = vectorizer.fit_transform(text_train)
transformed_text_test = vectorizer.transform(text_test)
filename_vectorizer = 'TfidfVectorizer.sav'
pickle.dump(vectorizer, open(filename_vectorizer, 'wb')) # Saving model

# Initialize Classifier
classifier = PassiveAggressiveClassifier(max_iter=100)

classifier.fit(transformed_text_train, label_train)

# Start Predict
predict = classifier.predict(transformed_text_test)

filename = 'ClassifierModel.sav'
pickle.dump(classifier, open(filename, 'wb')) # Saving model

# Get Accuracy Score
score = accuracy_score(label_test, predict)
print("Accuracy Score: %.2f%%" % (score*100))

X = vectorizer.transform(news['text'].astype('U'))
kscore = cross_val_score(classifier, X, news['label'].values, cv=5)
print(f'K Fold Accuracy: {round(kscore.mean()*100,2)}%')

print("\nClassification Report")
print(classification_report(label_test, predict))

print("\nConfusion Matrix")
print(confusion_matrix(label_test, predict))

# --------- Testing using saved model ----------- #

# print("**********Using saved model**********")
# loaded_tfid = pickle.load(open(filename_vectorizer, 'rb')) # Load saved vectorizer
# loaded_classifier = pickle.load(open(filename, 'rb')) # Load saved classifier model

# test_fake_news = pd.read_csv('datasets/Fake.csv')
# test_true_news = pd.read_csv('datasets/True.csv')
# test_fake_news['label'] = 'Fake'
# test_true_news['label'] = 'Real'
# test_fake_text = test_fake_news['text'].astype('U')

# transformed_text_to_predict = loaded_tfid.transform(test_text)

# predict_from_model = loaded_classifier.predict(transformed_text_to_predict)
# # print(predict_from_model)

# # Get Accuracy Score
# test_score = accuracy_score(label_test, predict_from_model)
# print("Accuracy= %.2f%%" % (score*100))

# --------- Testing using saved model ----------- #

#plot_cmat(label_test, predict) # Show Confusion Matrix