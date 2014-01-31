import webapp2
import math
import datetime
import jinja2
import os
import logging

from app.models import *
from app.elo_rating import *
from google.appengine.api import users

# initialise templating engine
jinja_environment = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)))

class MainHandler(webapp2.RequestHandler):
  def get(self):
    user = ActiveUser()
    if user.loaded:
      template_values = {
          "rankings": Competitor.ordered(),
          "user": user
          }
      template = jinja_environment.get_template('templates/index.html')
      self.response.out.write(template.render(template_values)) 

    else:
      greeting = ("You are not signed in. <a href=\"%s\">Join the competition</a>." %
           users.create_login_url("/"))
      self.response.out.write("<html><body>%s</body></html>" % greeting)

class ResultsHandler(webapp2.RequestHandler):
  def get(self):
    user = ActiveUser()
    if self.request.get("userid"):
      competitor = Competitor.by_id(self.request.get("userid"))
      logging.info("get results for %s " % (competitor.nickname))
      results = Result.all_for(competitor.userid)
    else:
      competitor = None
      results = Result.all_results()

    template_values = {
        'results': results, 
        'competitor': competitor,
        'user': user
        }
    template = jinja_environment.get_template('templates/results.html')
    self.response.out.write(template.render(template_values)) 

class AddResultHandler(webapp2.RequestHandler):
  def get(self):
    user = ActiveUser()
    
    winner_id = self.request.get("W")
    loser_id = self.request.get("L")

    if self.request.get("result_submit") == "submit" and winner_id != loser_id:
        
      winner = Competitor.by_id(winner_id)
      loser = Competitor.by_id(loser_id)
      winner_score = self.request.get("winner_score")
      loser_score = self.request.get("loser_score")
      
      Result.process_match_result(winner,loser,int(winner_score),int(loser_score))
           
      self.redirect("/")
    else:  
      template_values = {
          'competitors': Competitor.ordered(),
          'user': user
        }
      template = jinja_environment.get_template('templates/result.html')
      self.response.out.write(template.render(template_values)) 

    
class CalculatorHandler(webapp2.RequestHandler):
  def get(self):
    user = ActiveUser()
    competitors = Competitor.ordered()
    target,new_ratings = None,None
    if self.request.get("target"):
      target = Competitor.by_id(self.request.get("target"))
      new_ratings = EloRating.calculate_elo_rank(user.rating, target.rating)
      user_new_rating = new_ratings[0] # winner
      target_new_rating = new_ratings[1] # loser
      
    template_values = {
        'user': user,
        'target': target,
        'new_ratings': new_ratings,
        'competitors': competitors
        }
    template = jinja_environment.get_template('templates/calculator.html')
    self.response.out.write(template.render(template_values)) 


class ActiveUser():
  def __init__(self):
    # initialize with a appengine user object
    self.loaded = False
    if self.load():
      self.loaded = True
    
  def load(self):
    user = users.get_current_user()
    if user:
      u = self.find_or_add_user(user)
      self.userid = u.userid
      self.nickname = u.nickname
      self.rating = u.rating
      self.is_scorekeeper = u.is_scorekeeper
      self.include_in_rankings = u.include_in_rankings
      self.signout_url = users.create_logout_url("/")
      return True

  def find_or_add_user(self,user):
    if user:
      u = Competitor.by_id(user.user_id())
      if u is None:
        u = Competitor(
            userid = user.user_id(),
            nickname = user.nickname()
            )
        u.put()
        logging.info("added competitor " + u.userid)
      else:
        logging.info("recognised competitor " + u.userid)
      return u


