### pages of the website
# from operator import methodcaller
# from numpy import result_type
# import pandas as pd
from email.policy import default
from urllib import response
from flask import Blueprint, flash, jsonify, render_template, request, redirect, Markup, session, abort
# import os
from flask_login import login_required, current_user

from website.chatbot.chat import get_response
from . import db
from .models import Aok, NonAok, ScrapperSentence, User, WebsiteScrapper
import json
from .control import canScrap, checkIfAoK, doesAoKExist, getBaseURL, getModelsInfo, getRobotsURL, getSentenceFromDB, getSiteMaps, populateDatabaseWithAoKs, populateDatabaseWithNonAoKs, populateModelTable, removeFromSentences,  scrapWebsite, addAoK
# import website
from werkzeug.security import generate_password_hash
from flask_login import login_user


views = Blueprint("views", __name__)

# file_name = './website/static/actsOfKindness.xlsx'
# # file_name = 'actsOfKindness.xlsx'
# sheet_name = 'All_AoKs'
# description_column = 'Description'
# websiteURL = ""

# the route of our website
@views.route('/', methods=['GET', 'POST'])
def home():
    
    myEmail="faeq.rimawi@gmail.com"
     #add user to databse
    if User.query.filter_by(email=myEmail).first() is None: 
        new_user = User(email=myEmail, first_name="faeq", password=generate_password_hash("asd12345", method='sha256'))
        db.session.add(new_user)
        db.session.commit()
        login_user(new_user, remember=True)
    
    populateModelTable()
    populateDatabaseWithAoKs()
    populateDatabaseWithNonAoKs()  
        
                
    return render_template("home.html", user=current_user)


# the route of our website
@views.route('/chatbot', methods=['GET', 'POST'])
def chatbot():
    
    if request.method == 'POST':
        text = request.get_json().get("message")
        
        #TODO: check if text is valid
        
        responses = get_response(text)
        message = {"answers": responses}
        
        print("@@@ ", message)
        return jsonify(message)
        
            
    return render_template("chatbot.html", user=current_user)


@views.route('/guessAoK', methods=['POST', 'GET'])
def guessAoK():

    if request.method == 'POST':
        act = request.form.get('act')
        
        if act:
           probability = checkIfAoK(act)
        #    d =  jsonify(prob=probability) 
        #    return d   
           return render_template('guessAoK.html', user=current_user, prob=probability, act=act)
        else:
            flash("Please enter an act", category='error')

            
    return render_template("guessAoK.html", user=current_user, prob=-1, act="")


@views.route('/edit', methods=['GET', 'POST'])
def editAoK():
    
    if request.method == 'POST':
        aok = request.form.get('aok')
        
        if len(aok)<1:
            flash("Act too short!", category='error')
            
        else:
            new_aok = Aok(act=aok, user_id=current_user.id)
            db.session.add(new_aok)
            db.session.commit()
            
            flash("Act added successfully", category='success')
            
    return render_template("editAoK.html", user=current_user)



@views.route('/listofAoK')
def listofAoK():
 
    # testModelTable()
    # populateDatabase()
    
    
    # df = pd.read_excel(file_name, sheet_name=sheet_name, usecols=[description_column])
    aoks = Aok.query.all()
    nonaoks = NonAok.query.all()
    return render_template("listofAoK.html", aoks=aoks, nonaoks=nonaoks, user=current_user)
    # return df.to_html()
 
 
@views.route('/api/aokdata', methods=["POST"])
def aokdata():
   
    #  return {'data': [aok.to_dict() for aok in Aok.query]}
    query = Aok.query
    data = request.get_json()
    
    if 'operation' not in data:
        abort(400) 

    operation = data['operation']
    
    match operation:
        case 'fetch-all':
            return [aok.to_dict() for aok in query]

        case _:
            print("@@@ nothing")
            return []
       
       
@views.route('/api/nonaokdata', methods=['POST'])
def nonaokupdate():
    
    query = NonAok.query
    data = request.get_json()
    
    if 'operation' not in data:
        abort(400) 

    operation = data['operation']
    
    match operation:
        case 'fetch-all':
            return [nonaok.to_dict() for nonaok in query]
        case _:
            return []

      
@views.route('/api/actdata', methods=['POST'])
def actdataupdate():
    
    data = request.get_json()
    query = ScrapperSentence.query
     
    if 'operation' not in data:
        abort(400)
    
    operation = data['operation']    
    
    
    match operation:
        case 'fetch-all':
            website = data['data']  
            if website:
             
    
                websiteID = WebsiteScrapper.query.filter_by(url=str(website)).first()
                
                if websiteID:
            
                    return [sent.to_dict() for sent in query.filter_by(website_id=websiteID.id)]
                else:
                    return [] 
        case 'updateAct':
            oldAndNewAct = data['data']
            if len(oldAndNewAct) <2:
                return ''
            
            oldAct = oldAndNewAct[0]
            newAct = oldAndNewAct[1]
            
            field = 'text'
            sentences = query.filter_by(text=str(oldAct)).all()
            for sent in sentences:
                setattr(sent, field, newAct)
                db.session.commit()
            
            return jsonify({"response": "success"})
        
        case 'removeAct':
            actID = data['data']
            print("delete id ", actID)
            if actID is None:
                return jsonify({})
            
            act = query.get(int(actID))
            
            
            
            if act is None:
                return jsonify({})
            
            db.session().delete(act)
            db.session.commit()
            return jsonify({"response": "success"})
            
           
           
@views.route('/delete-AoK', methods=['POST'])
def delete_AoK():
    aok = json.loads(request.data)
    aokId = aok['aokId']      
    
    aok = Aok.query.get(aokId)
    if aok.user_id == current_user.id:
        db.session().delete(aok)
        db.session.commit()
        
    return jsonify({})


@views.route('/add-AoK', methods=['POST'])
def add_AoK():

    sent = json.loads(request.data)
    sentID = sent['actID']   
    # websiteURL = aok['websiteURL']
    
    # if type(sentStr) != str:
    #     sentStr = str(sentStr)
          
    sent = getSentenceFromDB(sentID)
        
    if sent is None:        
        return jsonify({'message':'error'})
                    
    # check if already exists in the database
    inDB = doesAoKExist(sent.text)
    
    if inDB:
        result = jsonify({'message':'exists'})
    
        return result
    else: 
        result = addAoK(sent.text, sent.get_website()) 
        
      
        if result is not None:
            removeFromSentences(sent.text)
            res = {'message':'added'} 
            return jsonify(res)
        else:
            return jsonify({'message':'error'})


@views.route('/update-prob', methods=['POST'])
def update_prob():
     aok = json.loads(request.data)
     aok_str = aok['aok']
     
     if type(aok_str) != str:
        aok_str = str(aok_str)
        
     prob = checkIfAoK(aok_str)  
     
     return jsonify({'prob':prob}) 
        
        
    
    
@views.route("/aok-scrapper", methods=["POST", "GET"])
def aokScrapper():
    
    if request.method == 'POST':
     
        websiteURL = request.form.get('websiteURL')  
               
      
        sents =  scrapWebsite(websiteURL)
      
        # acts_and_probs = {'data': [{"sents":"1"}, {"sents":"1"}],
        # 'total': len(sents),
        # }
      
        #get sitemap
        sitemap = {'sitemap':getSiteMaps(websiteURL)}
     
    
        # return render_template("scrapper.html", user=current_user, websiteURL=websiteURL, act_probs=act_probs, canScrap=True)
        isPer = canScrap(websiteURL)
        
        robotUrl = getRobotsURL(websiteURL)
        baseURL = getBaseURL(websiteURL)
        if not isPer:
           flash(Markup("Scraping may not be permissible on this webpage per the website's permissions. For more info, see: <a href=\""+robotUrl+"\" target='_blank' class=\"alert-link\">"+robotUrl + "</a>") , category='warning')
            
     
        return render_template("scrapper.html", user=current_user, websiteURL=websiteURL, robotsURL=robotUrl, baseURL=baseURL, sitemap=sitemap) 
    
    # get all sites already visited
    siteURLs = [url.url for url in WebsiteScrapper.query.all()]
    print("@@@@ ", siteURLs)
    return render_template("scrapper.html", user=current_user)



@views.route("/aok-model", methods=["POST", "GET"])
def AoKModel():
    
    info = getModelsInfo()
    
    return render_template("AoKModel.html", user=current_user, models=info)
  
  
    
@views.get("/toggle-theme")
def toggle_theme():
    current_theme = session.get("theme")
    if current_theme == "dark":
        session["theme"] = "light"
    else:
        session["theme"] = "dark"

    return redirect(request.args.get("current_page"))


             
    
       
    
# @views.route('/api/actdata')
# def actdata():
   
#     #  return {'data': [aok.to_dict() for aok in Aok.query]}
#     query = ScrapperSentence.query
    
#     website = request.args.get('website')
#     websiteID = WebsiteScrapper.query.filter_by(url=website)
    
#     print(" @@@", website, " id ", websiteID)

#     return [sent.to_dict() for sent in query.filter_by(url_id=websiteID)]

#    # search filter
#     search = request.args.get('search')
#     if search:
#         query = query.filter(db.or_(
#             ScrapperSentence.text.like(f'%{search}%')
            
#         ))
#     total = query.count()

#    # sorting
#     sort = request.args.get('sort')
#     if sort:
#         order = []
#         for s in sort.split(','):
#             direction = s[0]
#             name = s[1:]
#             if name not in ['text', 'prob_aok']:
#                 # name = 'text'
#                 continue
#             col = getattr(ScrapperSentence, name)
#             if direction == '-':
#                 col = col.desc()
#             order.append(col)
#         if order:
#             query = query.order_by(*order)


#    # pagination
#     start = request.args.get('start', type=int, default=-1)
#     length = request.args.get('length', type=int, default=-1)
#     if start != -1 and length != -1:
#         query = query.offset(start).limit(length)

#     # response
#     return {
#         'data': [sent.to_dict() for sent in query],
#         'total': total,
#     }
       
 
    
# @views.route('/api/aokdata', methods=['POST'])
# def aokupdate():
#     data = request.get_json()
#     if 'id' not in data:
#         abort(400)
        
#     aok = Aok.query.get(data['id'])
#     for field in ['act', 'source', 'date']:
#         if field in data:
#             setattr(aok, field, data[field])
#     db.session.commit()
#     return '', 204
           
           
# @views.route('/api/nonaokdata')
# def nonaokdata():
   
#     #  return {'data': [aok.to_dict() for aok in Aok.query]}
#     query = NonAok.query


#    # search filter
#     search = request.args.get('search')
#     if search:
#         query = query.filter(db.or_(
#             NonAok.act.like(f'%{search}%'),
#             NonAok.source.like(f'%{search}%')
#         ))
#     total = query.count()

#    # sorting
#     sort = request.args.get('sort')
#     if sort:
#         order = []
#         for s in sort.split(','):
#             direction = s[0]
#             name = s[1:]
#             if name not in ['act', 'source', 'date']:
#                 name = 'act'
#             col = getattr(NonAok, name)
#             if direction == '-':
#                 col = col.desc()
#             order.append(col)
#         if order:
#             query = query.order_by(*order)


#    # pagination
#     start = request.args.get('start', type=int, default=-1)
#     length = request.args.get('length', type=int, default=-1)
#     if start != -1 and length != -1:
#         query = query.offset(start).limit(length)

#     # response
#     return {
#         'data': [aok.to_dict() for aok in query],
#         'total': total,
#     }
 
 
 
# @views.route("/api/data")
# def data():
    # # query = request.query_string
    
    # df = pd.read_excel(file_name, sheet_name=sheet_name, usecols=[description_column])[0:100]


    # # # search filter
    # search = request.args.get('search[value]')
    # if search:
    #     df = df.apply(lambda row: row.astype(str).str.contains(f'%{search}').any(), axis=1)
    
    # total_filtered = df.count()

    # # total_filtered = query.count()

    # # # sorting
    # # order = []
    # # i = 0
    # # while True:
    # #     col_index = request.args.get(f'order[{i}][column]')
    # #     if col_index is None:
    # #         break
    # #     col_name = request.args.get(f'columns[{col_index}][data]')
    # #     if col_name not in ['Description']:
    # #         col_name = 'Description'
    # #     descending = request.args.get(f'order[{i}][dir]') == 'desc'
    # #     col = getattr(df, col_name)
    # #     if descending:
    # #         col = col.desc()
    # #     order.append(col)
    # #     i += 1
    # # if order:
    # #     query = query.order_by(*order)

    # # # pagination
    # # start = request.args.get('start', type=int)
    # # length = request.args.get('length', type=int)
    # # query = df.offset(start).limit(length)
    

    # # response
    # return {
    #     # 'data': [user.to_dict() for user in query],
    #     'recordsFiltered': total_filtered,
    #     # 'recordsTotal': query.count(),
    #     # 'draw': request.args.get('draw', type=int),
    #     'data' : [df.to_json()],
    # }





# @views.route("/aok-scrapper", methods=["POST", "GET"])
# def aokScrapper():
    
#     if request.method == 'POST':
#         # data = json.loads(request.data)
#         # websiteURL = data['websiteURL']         
#         # sentences = scrapWebsite(websiteURL)
#         # act_probs = []
        
#         # if sentences:
#         #     for sent in sentences:

#         #         prob = checkIfAoK(sent)
#         #         pair = {'act':sent, 'prob':prob}
#         #         act_probs.append(pair)
        
            
#         # # return render_template("scrapper.html", user=current_user, websiteURL=websiteURL, act_probs=act_probs, canScrap=True)
#         # isPer = canScrap(websiteURL)
        
#         # if( not isPer):
#         #    robotUrl = getRobotsURL(websiteURL)
#         #    flash(Markup("Scraping may not be permissible on this webpage per the website's permissions. For more info, see: <a href=\""+robotUrl+"\" target='_blank' class=\"alert-link\">"+robotUrl + "</a>") , category='warning')
      
#         # return jsonify({"result":"success", "acts":json.dumps(act_probs)});    
#         websiteURL = request.form.get('websiteURL')  
               
#         # print("@@@ ", websiteURL) 
        
#         # acts_and_probs = {"data":scrapWebsite(websiteURL)}
#         sents =  scrapWebsite(websiteURL)
#         # print(setns)
#         acts_and_probs = {'data': [{"sents":"1"}, {"sents":"1"}],
#         'total': len(sents),
#         }
#         # print(acts_and_probs)
#         # act_probs = []
        
#         # if sentences:
#         #     for sent in sentences:

#         #         prob = checkIfAoK(sent)
#         #         pair = (sent, prob)
#         #         act_probs.append(pair)
            
        
#         #get sitemap
#         sitemap = {'sitemap':getSiteMaps(websiteURL)}
#         # sitemap = getSiteMaps(websiteURL)
    
#         # return render_template("scrapper.html", user=current_user, websiteURL=websiteURL, act_probs=act_probs, canScrap=True)
#         isPer = canScrap(websiteURL)
        
#         robotUrl = getRobotsURL(websiteURL)
#         baseURL = getBaseURL(websiteURL)
#         if not isPer:
#            flash(Markup("Scraping may not be permissible on this webpage per the website's permissions. For more info, see: <a href=\""+robotUrl+"\" target='_blank' class=\"alert-link\">"+robotUrl + "</a>") , category='warning')
            
#         # data = {"acts_probs": acts_and_probs, 
#         #         "sitemap":{"sites" : sitemap,
#         #                    "scrappingPermitted":isPer,
#         #                    "robotURL": robotUrl,
#         #                    "baseURL": baseURL}
#         #         }     
#         # return jsonify(data)    
#         return render_template("scrapper.html", user=current_user, websiteURL=websiteURL, robotsURL=robotUrl, baseURL=baseURL, acts_and_probs=acts_and_probs, sitemap=sitemap) 
    
#     return render_template("scrapper.html", user=current_user)


# @views.route('/api/aokdata')
# def aokdata():
   
#     #  return {'data': [aok.to_dict() for aok in Aok.query]}
#     query = Aok.query


#    # search filter
#     search = request.args.get('search')
#     if search:
#         query = query.filter(db.or_(
#             Aok.act.like(f'%{search}%'),
#             Aok.source.like(f'%{search}%')
#         ))
#     total = query.count()

#    # sorting
#     sort = request.args.get('sort')
#     if sort:
#         order = []
#         for s in sort.split(','):
#             direction = s[0]
#             name = s[1:]
#             if name not in ['act', 'source', 'date']:
#                 name = 'act'
#             col = getattr(Aok, name)
#             if direction == '-':
#                 col = col.desc()
#             order.append(col)
#         if order:
#             query = query.order_by(*order)


#    # pagination
#     start = request.args.get('start', type=int, default=-1)
#     length = request.args.get('length', type=int, default=-1)
#     if start != -1 and length != -1:
#         query = query.offset(start).limit(length)

#     # response
#     return {
#         'data': [aok.to_dict() for aok in query],
#         'total': total,
#     }
       
       
# @views.route('/api/aokdata', methods=['POST'])
# def aokupdate():
#     data = request.get_json()
#     if 'id' not in data:
#         abort(400)
        
#     aok = Aok.query.get(data['id'])
#     for field in ['act', 'source', 'date']:
#         if field in data:
#             setattr(aok, field, data[field])
#     db.session.commit()
#     return '', 204