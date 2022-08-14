from email.policy import default
from email.quoprimime import unquote
from sqlalchemy import PrimaryKeyConstraint
from . import db
from flask_login import UserMixin
from sqlalchemy.sql import func
# from sqlalchemy import Enum
import enum

class ActType(enum.Enum):
        NORMAL= "Normal Act"
        ANTI_SOCIAL = "Anit-Social Act"
            
            
class Level(enum.Enum):
    Very_High = "Very High"
    High= "High"
    Medium = "Medium"
    Low = "Low"
    Very_Low = "Very Low"            
    
    
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True)
    password = db.Column(db.String(150))
    first_name = db.Column(db.String(150))
    acts = db.relationship('Aok') # link a user to their aoks (need to capitalise the name of the calss)
    non_aok_acts = db.relationship('NonAok')
    websites_scrapped = db.relationship('WebsiteScrapper')
    
    
    
    
class Aok(db.Model):
    
    __name__="aok"
    
    id = db.Column(db.Integer, primary_key=True)
    act = db.Column(db.String(1000))
    date = db.Column(db.DateTime(timezone=True), default=func.now())
    source = db.Column(db.String(1000))
    categories = db.relationship('AokCategories', cascade = 'all, delete-orphan', lazy = 'dynamic')
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    nlp_models = db.relationship('ModelAok', cascade = 'all, delete-orphan', lazy = 'dynamic')
    
    def to_dict(self):
        return {
            'id': self.id,
            'act': self.act,
            'date': self.date,
            'source': self.source
        }
    
    

class NonAok(db.Model):
    
    __name__ = "nonaok"
    
    id = db.Column(db.Integer, primary_key=True)
    act = db.Column(db.String(1000))
    date = db.Column(db.DateTime(timezone=True), default=func.now())
    type = db.Column(db.Enum(ActType))
    source = db.Column(db.String(1000))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    nlp_models = db.relationship('ModelNonAok', cascade = 'all, delete-orphan', lazy = 'dynamic')
    
    def to_dict(self):
        return {
            'id': self.id,
            'act': self.act,
            'date': self.date,
            'type': self.type,
            'source': self.source
        }
        
    

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(1000), unique=True)
    acts = db.relationship('AokCategories', cascade = 'all, delete-orphan', lazy = 'dynamic')
    
    def to_dict(self):
        return {
            'name': self.name
        }
        

## association table between categories and aok showing which aoks belong to which categories      
class AokCategories(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'))  
    aok_id =  db.Column(db.Integer, db.ForeignKey('aok.id'))
      
    
class NLPModel(db.Model):
    id = db.Column(db.Integer, primary_key=True)    
    model = db.Column(db.PickleType)
    features = db.Column(db.PickleType)
    aoks = db.relationship('ModelAok', cascade = 'all, delete-orphan', lazy = 'dynamic')
    non_aoks = db.relationship('ModelNonAok', cascade = 'all, delete-orphan', lazy = 'dynamic')
    

## association table between models and aok showing which aoks belong to which models    
class ModelAok(db.Model):
    id = db.Column(db.Integer, primary_key=True)  
    aok_id =  db.Column(db.Integer, db.ForeignKey('aok.id'))
    model_id = db.Column(db.Integer, db.ForeignKey('nlp_model.id'))
    

## association table between models and non-aok showing which non-aoks belong to which models    
class ModelNonAok(db.Model):
    id = db.Column(db.Integer, primary_key=True)  
    non_aok_id =  db.Column(db.Integer, db.ForeignKey('non_aok.id'))
    model_id = db.Column(db.Integer, db.ForeignKey('nlp_model.id'))
        
        
class WebsiteScrapper(db.Model):
    id = db.Column(db.Integer, primary_key=True)  
    url = db.Column(db.String(1000), unique=True)
    date = db.Column(db.DateTime(timezone=True), default=func.now())
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    sentences = db.relationship('ScrapperSentence', cascade = 'all, delete-orphan', lazy = 'dynamic') 
    # sitemaps = db.relationship('Sitemap')   
    
    
    # def get_sitemaps(self):
    #     return Sitemap.query.with_entities(Sitemap.url).filter_by(self.id).all()
    
    
class ScrapperSentence(db.Model):
     id = db.Column(db.Integer, primary_key=True) 
     text = db.Column(db.String(1000))
     prob_aok =   db.Column(db.Float)
     website_id = db.Column(db.Integer, db.ForeignKey('website_scrapper.id'))
        
     def to_dict(self):
        return {
            'id': self.id,
            'text': self.text,
            'prob_aok': float(self.prob_aok)
        }
        
     def get_website(self):
         website = WebsiteScrapper.query.filter_by(id=self.website_id).first()   
         
         if website is not None:
             return website.url
            
           
                
class Sitemap(db.Model):
      id = db.Column(db.Integer, primary_key=True) 
      url = db.Column(db.String(1000), unique=True)
      sites = db.relationship('Site', cascade = 'all, delete-orphan', lazy = 'dynamic') 
    #   website_id = db.Column(db.Integer, db.ForeignKey('website_scrapper.id'))
        
      def to_dict(self):
        return {
            'url': self.url,
            'sites': [ {'url':str(site.url), 'scrapped':site.isScrapped()} for site in Site.query.filter_by(sitemap_id=self.id).all()]
        }
        
      def get_sitemaps(baseURL):
        sitemaps = db.session.query(Sitemap).filter(Sitemap.url.like(f'{str(baseURL)}%')).all()
        return sitemaps
        
    
class Site(db.Model):
      id = db.Column(db.Integer, primary_key=True) 
      url = db.Column(db.String(1000), unique=True)
      level_aok =   db.Column(db.Enum(Level))
      priority = db.Column(db.String(1000))
      change_frequency = db.Column(db.String(1000))
      last_modified = db.Column(db.String(1000))
      sitemap_id = db.Column(db.Integer, db.ForeignKey('sitemap.id'))
      last_accessed = db.Column(db.DateTime(timezone=True), default=func.now())
      
      
      def get_sitemap(self):
          return Sitemap.query.filter_by(id=self.sitemap_id).first()
      
      def isScrapped(self):
          scrap = WebsiteScrapper.query.filter_by(url=self.url).first()
          
          if scrap is None:
              return False
          
          return True
      

      
     
    
    