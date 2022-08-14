# from fileinput import filename
# from genericpath import exists
# from glob import glob
# from multiprocessing.dummy import active_children

from datetime import datetime
import pickle
from urllib.request import urlopen
from sklearn.cluster import dbscan
# from sre_constants import FAILURE, SUCCESS
# from xmlrpc.client import Boolean
# from flask import url_for
from sklearn.feature_extraction.text import TfidfTransformer, CountVectorizer
from bs4 import BeautifulSoup as bs
import requests
# import re
import nltk
# nltk.download()
from sqlalchemy import exists
# import trafilatura
# import json
# import numpy as np
# from requests.models import MissingSchema
from .models import Aok, ModelAok, ModelNonAok, NLPModel, NonAok, ScrapperSentence, Site, Sitemap, WebsiteScrapper
from . import db
from flask_login import current_user
import urllib.robotparser as urobot
from urllib.parse import urlparse
# import urllib.request
# import ssl
import string
import pandas as pd
# from .views import websiteURL
 
model = None

features_file = None

loaded_vec = None


def load_Model_and_Features():
    global model
    global features_file
    
    if not model:
        model = pickle.load(open('./website/static/AoK_classifier_model.pkl', 'rb'))
      
    if not features_file:
       features_file = pickle.load(open("./website/static/AoK_features.pkl", "rb"))


def addAoK(aok, source):
    
    if len(aok)<1:
        return None

    ## try to find it in the sentence table
    # scrapperSentence = ScrapperSentence.query.text.filter_by(text=str(aok)).first()

    # websiteURL = scrapperSentence.get_website() if scrapperSentence is not None else ""
  
    new_aok = Aok(act=aok, user_id=current_user.id, source=str(source))
    db.session.add(new_aok)
    db.session.commit()
    
    return new_aok
 
    
def removeFromSentences(aokStr):
     
    sentences = ScrapperSentence.query.filter_by(text=str(aokStr)).all()
     
    # print("sent to delete: ", sentences)

    for sent in sentences:    
        db.session.delete(sent)
        db.session.commit()
    
    
def checkIfAoK(act):
    global model
    global features_file
    global loaded_vec
    
    if not model:
       load_Model_and_Features()

    if not loaded_vec:
        loaded_vec = CountVectorizer(decode_error="replace",vocabulary=features_file)
 
            
    converted_data = loaded_vec.fit_transform([act])
    transformer = TfidfTransformer()
    text = transformer.fit_transform(converted_data).toarray()
    y_pred = model.predict_proba(text)
        
    prob = y_pred[0][1]*100
    
    # print("#### act:", act, " prob:", prob)
    
    return prob


def scrapWebsite(websiteURL):
    
    ### need to check url states (but already check by the client side)
    
    # check in the db if the website already scrapped before
    site = scrapeAndSave(websiteURL)
    
    if site is None:
        return 
    
    # print("###: returning from db")
    sents =  [sent.to_dict() for sent in ScrapperSentence.query.filter_by(website_id=int(site.id)).all()]
    # print(sents)
   
    return sents


def scrapeAndSave(websiteURL):
    '''
    finds all possible sentences in the given url, filters them (removes repetitions, tags, etc), 
    and saves them to database (including the URL)  
    
    paramter: website url as a string
    returns a WebsiteScrapper object or None if failed
    ''' 
    
    if websiteURL is None:
        return
    
    site = WebsiteScrapper.query.filter_by(url=str(websiteURL)).first()

    if site is not None:
        return site
    
    
    page = requests.get(websiteURL)
    soup = bs(page.content, features="html.parser")
    # text = soup.find_all("<li>")
    sents = soup.find_all(text=True)
    
    if len(sents) == 0:
        return
    
    sents = processWebsiteScrapText(sents)
    sents = removeJunkSentences(sents)
       
    #add to db
    # print("###: adding to dB")
    site = WebsiteScrapper(url=str(websiteURL))
   
    db.session.add(site)     
    db.session.commit()  
    
    # could do this in multi-threading (later!)
    dbSents = []
    for sent in sents:
        prob = checkIfAoK(sent)
        newSent = ScrapperSentence(text=str(sent),website_id=site.id, prob_aok=prob)
        dbSents.append(newSent)
     
    db.session.add_all(dbSents)
    db.session.commit()    
            
            
    return site    
    
    
def processWebsiteScrapText(text):
    # returns the set of sentences in the given text
   
    # Remove unwanted tag elements:
    cleaned_text = ''
    blacklist = [
        '[document]',
        'noscript',
        'header',
        'html',
        'meta',
        'head', 
        'input',
        'script',
        'style',
        'div',]
    
    # Then we will loop over every item in the extract text and make sure that the beautifulsoup4 tag
    # is NOT in the blacklist
    for item in text:
        if item.parent.name not in blacklist:
            cleaned_text += '{} '.format(item)
            
      # Remove any tab separation and strip the text:
    cleaned_text = cleaned_text.replace('\t', '')
    # return cleaned_text.strip()
    cleaned_text.strip()
    
    sentences = nltk.sent_tokenize(cleaned_text)
    new_sents = []
    for sent in sentences:
        sent = ' '.join(sent.split())
        if sent:
            # print(sent)
            new_sents.append(sent)
            
    return new_sents        
    

def removeJunkSentences(sentences):
    ### removes all sentences that are
    ## duplicates
    ## only numbers
    ## contain specific wording 
    
    # new_sents = []
    
    
    # new_sents = [i for i in sentences if not i.translate(str.maketrans('', '', string.punctuation)).isnumeric()]
     
    new_sents2 = [] 
    
    for sent in sentences:
        
        # not duplicate
        if not sent.translate(str.maketrans('', '', string.punctuation)).isnumeric() and not sent in new_sents2:
            new_sents2.append(sent)
            
    return new_sents2
        
    
def getSiteMaps(url):
    
    sitemaps = saveSiteMaps(url)
    
    jsonSites = []
    
    for sitemap in sitemaps:
       jsonSites.append(sitemap.to_dict()) 
        
    return jsonSites
 


def saveSiteMaps(url):
    '''
    1- finds all sitemaps in using the given url
    2- loops over the sites found in each sitemap
    3- if a site has one of the keywords (e.g., aok or acts of kindness) then they will be added, otherwise removed (This can be should be updated to include levels of potentially containing aoks)
    
    parameters: url as string
    returns: a list of Sitemap objects
    '''
    
    if url is None:
        return
    
    ## check if already in db
    baseURL = getBaseURL(url)
    # urlObj = Site.query.filter_by(url=url).first()
    sitemaps = Sitemap.get_sitemaps(baseURL)
    
    if len(sitemaps) != 0:
        # print("### there are site maps for ", url)
        # print(sitemaps)
        return sitemaps
    
    
    rp = urobot.RobotFileParser()
    
    
    # websiteObj = WebsiteScrapper.query.filter_by(url=str(url)).first()
    
    rp.set_url(baseURL + "/robots.txt")
    # print(baseURL + "/robots.txt")
    rp.read()
    
    all_sitemaps = []
    
    all_sitemaps = rp.site_maps()
    
    #  baseURL = getBaseURL(url)
     
    # robotsURL = baseURL + "/robots.txt"
    # xmlDict = {}
  
    if not all_sitemaps:
        #try sitemap.xml with base url
        all_sitemaps = [baseURL + "/sitemap.xml"]
       
    # more_sitemaps = []  
    #does it have more sitemaps in the basic sitemap.xml
    for sitemap in all_sitemaps:
        more_sitemaps = check_has_more_sitemaps(sitemap)
        
     
    if more_sitemaps:
        all_sitemaps = more_sitemaps
        
    # if all_sitemaps:
    #     sitemaps = all_sitemaps
       
    # print("####: ", all_sitemaps)
        
    sitemapsArray = []
    # allSites = []
    
    for sitemap in all_sitemaps:
        # print("sitemap: ", sitemap)
        # if websiteObj is not None:
        newSiteMap = Sitemap(url=sitemap)  
        db.session.add(newSiteMap)
        db.session.commit()
        
        sites = parse_sitemap(newSiteMap)
        
        
        if sites is not None and len(sites) >0:
            db.session.add_all(sites)
            db.session.commit() 
            sitemapsArray.append(newSiteMap)
        else:
            Sitemap.query.filter_by(id=newSiteMap.id).delete(synchronize_session=False)
            db.session.commit()
       
                   
    return sitemapsArray
   
    
 
def parse_sitemap(sitemapURL):

    '''
    returns all  sites found in the sitemap
      
    parameters: sitemapURL: is a database object of table Sitemap
    returns: list of Site objects
    '''
    if sitemapURL is None:
        return None
    
    sitemapStr = str(sitemapURL.url)
    
    resp = requests.get(sitemapStr)

    # we didn't get a valid response, bail
    if 200 != resp.status_code:
        return None
    
    
    # BeautifulStoneSoup to parse the document
    soup = bs(resp.content, features='xml')

    # find all the <url> tags in the document
    urls = soup.findAll('url')

    # no urls? fail
    if not urls:
        return None

    # storage for later...
    sites = []

    #extract what we need from the url
    for u in urls:
        loc = u.find('loc').string if u.find('loc') else None

        # skips url if its path is not potentially one that has kindness acts
        if not loc or not is_potentially_kindness_url(loc):
            continue
            
        prio =  u.find('priority').string if u.find('priority') else None 
        change = u.find('changefreq').string if u.find('changefreq') else None
        last = u.find('lastmod').string if u.find('lastmod') else None
        
        newSite = Site(url=loc, priority=prio,change_frequency=change,last_modified=last, sitemap_id=sitemapURL.id)
        
        sites.append(newSite)
    
    return sites
        
    # return sites


def check_has_more_sitemaps(sitemap):
    
    resp = requests.get(sitemap)

    # we didn't get a valid response, bail
    if 200 != resp.status_code:
        return False

    # BeautifulStoneSoup to parse the document
    soup = bs(resp.content, features='xml')


    # find all the <url> tags in the document
    urls = soup.findAll('sitemap')
    
     # no urls? bail
    if not urls:
        return False

    # storage for later...
    out = []

    #extract what we need from the url
    for u in urls:
        loc = u.find('loc').string if u.find('loc') else None
        out.append(loc)
        
    return out

    return
    
def get_kindness_urls(urls):
    ### processes the given urls to return the top most related to kindness
    ### that be: onces that mention acts of kindness (preferrably as a whole unit) or just kindness in the path (not the base)
    
    filteredURLs = []
    
    for url in urls:
        if is_potentially_kindness_url(url):
            filteredURLs.append(url)
            
    return filteredURLs
   
    
def is_potentially_kindness_url(url): 
    ### checks if the given url is potentially good to look for aoks
    ### criteria: onces that mention acts of kindness (preferrably as a whole unit) or just kindness in the path (not the base)
    parsedURL = urlparse(url)
    
    path = str(parsedURL.path)
    
    matches =["kindness", "kind-", "kind_", "aok","act-of-kindness","act_of_kindness", "acts-of-kindness", "acts_of_kindness", "kindness-acts", "kindness_acts", "kindness-act", "kindness_act"]
    
    if path:
       # contains kindness word
       if any(x in path for x in matches):
           return True
    
    return False  
 
 
            
def canScrap(url):
    rp = urobot.RobotFileParser()
    
    baseURL = getBaseURL(url)
     
    robotsURL = baseURL + "/robots.txt"
      
    rp.set_url(robotsURL)
    
    rp.read()
    
    # parsedURL = urlparse(url)
    
    # path = parsedURL.path  
   
   ## almost always this returrns false
    # print("######## ", url, " ", rp.can_fetch("*", url))
    return rp.can_fetch("*", url)

      
        
    
def getBaseURL(url):
    parsedURL = urlparse(url)
    
    base = parsedURL.scheme + "://"+ parsedURL.netloc
    
    return base

def getRobotsURL(url):
    
    return getBaseURL(url) + "/robots.txt"
    

def doesAoKExist(aokDescription):
    
   res = db.session.query(exists().where(Aok.act==aokDescription)).scalar()  
   
#    if aokDescription.contains("RAK"):
#    print("### res checking ", aokDescription, ": ", res)  
   return res

def getSentenceFromDB(sentID):
    
    if sentID is None:
        return None
    
    sentence = ScrapperSentence.query.filter_by(id=sentID).first()
    
    return sentence
     

def populateModelTable():
    global model
    global features_file
    
    if not model:
        load_Model_and_Features()
    
   
    if len(NLPModel.query.all()) ==0 : 
        # print("###  creating a new model")       
        new_model = NLPModel(model=str(model), features=features_file)
        
        if new_model:
            db.session.add(new_model)
            res = db.session.commit()  
        else:
            print("problem creating a new model")  
        
    # newAok = Aok(act="testing")
    # db.session.add(newAok)
    # db.session.commit()
    
    # models = NLPModel.query.all()
    
    # for model in models:
    #     newModelAok = ModelAok(model_id=model.id, aok_id=newAok.id)
    #     db.session.add(newModelAok)
    #     db.session.commit()
    #     print(str(model.model))   
         
    
def getModelsInfo():
      ### info: name, # of aok, # of non-aok
      models = NLPModel.query.all()
      
      modelsInfo = []
      for model in models:
          name = str(model.model)
        #   print("###: ", model.aoks)
        #   numOfAoK = len(ModelAok.query.filter_by(model_id=model.id).all())
          numOfAoK = model.aoks.count()
          numOfNonAoK = model.non_aoks.count()
          record = [name, numOfAoK, numOfNonAoK]
          modelsInfo.append(record)
        #   print("## rec: ", record)
          
      return modelsInfo
  
  
def populateDatabaseWithAoKs():
    
    # already loaded
    if Aok.query.first() is not None:
        return
    
    # file_name = url_for('website/static', filename='actsOfKindness.xlsx')
    file_name = './website/static/actsOfKindness.xlsx'
    sheet_name = 'All_AoKs'
    description_column = 'Description'
    trained_col = 'trained'
    df = pd.read_excel(file_name, sheet_name=sheet_name, usecols=[description_column, trained_col])
    
    model = NLPModel.query.first()
    
    if model is None:
        return 
    
    newAoks = []
    newModelAoKs = []
    for element in df.values:
    
        if len(element) >0 :
            newAok = Aok(act=element[0])
            if newAok:
                newAoks.append(newAok)
                # print(newAok.act)

                isTrained = element[1]
                if isTrained == 'yes':        
                    newModelAok = ModelAok(model_id=model.id, aok_id=newAok.id)
                    newModelAoKs.append(newModelAok)
                    
                    
    if len(newAoks) > 0:
        db.session.add_all(newAoks)
        db.session.commit()    
        
    if len(newModelAoKs) >0:
        db.session.add_all(newModelAoKs)
        db.session.commit()    
        
    return      
          

def populateDatabaseWithNonAoKs():
    
    # already loaded
    if NonAok.query.first() is not None:
        # print("already added non-aoks")
        return
    
    # file_name = url_for('website/static', filename='actsOfKindness.xlsx')
    file_name = './website/static/actsOfKindness.xlsx'
    sheet_name = 'All_NonAoks'
    description_column = 'Description'
    trained_col = 'trained'
    df = pd.read_excel(file_name, sheet_name=sheet_name, usecols=[description_column, trained_col])
    
    model = NLPModel.query.first()
    
    if model is None:
        return
    
    newNonAoks = []
    newModelNonAoKs = []
    for element in df.values:
    
        if len(element) >0 :
            newNonAok = NonAok(act=element[0])
            if newNonAok:
                newNonAoks.append(newNonAok)
                # print(newAok.act)

                isTrained = element[1]
                if isTrained == 'yes':        
                    newModelNonAok = ModelNonAok(model_id=model.id, non_aok_id=newNonAok.id)
                    newModelNonAoKs.append(newModelNonAok)
                    
                    
    if len(newNonAoks) > 0:
        db.session.add_all(newNonAoks)
        db.session.commit()    
        
    if len(newModelNonAoKs) >0:
        db.session.add_all(newModelNonAoKs)
        db.session.commit()    
        
    return                
      
        
        
     