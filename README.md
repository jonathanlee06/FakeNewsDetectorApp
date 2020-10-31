# Fake News Detector App
Fake News Detector App is a Fake News Detection website developed by Jonathan Lee as part of the Final Year Project (FYP). The aim of the application is to help reduce human contact during check-in process at campus.

## Overview
With the rapid growing rate of information over the internet, the topic of fake news detection on social media has recently attracted tremendous attention. The basic countermeasure of comparing websites against a list of labeled fake news sources is inflexible, and so a machine learning approach is desirable. This project aims to use Natural Language Processing (NLP) and Passive Agressive Classifier to detect fake news directly, based on the text content of news articles.

## Objectives
1. To investigate and identify the key features of fake news
2. To design and develop a machine learning based fake news detection system
3. To validate the effectiveness of a machine learning based fake news detection system

## Dataset Overview

- train.csv: A full training dataset with the following attributes:
    - id: unique id for a news article
    - title: the title of a news article
    - author: author of the news article
    - text: the text of the article; could be incomplete
    - label: a label that marks the article as potentially unreliable
        - 1: Fake news/Unreliable news
        - 0: Real News/Reliable news

- test.csv: A testing training dataset with all the same attributes at train.csv without the label.

Dataset Source: [https://www.kaggle.com/c/fake-news/data](https://www.kaggle.com/c/fake-news/data)

## Machine Learning Model
- PassiveAgressive Classifier