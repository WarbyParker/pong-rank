
import logging
import operator
import datetime
from google.appengine.ext import db

from app.elo_rating import *

BASE_RANK = 1200.0

class Competitor(db.Model):
  userid = db.StringProperty()
  nickname = db.StringProperty()
  rating = db.FloatProperty(default=BASE_RANK)
  include_in_rankings = db.BooleanProperty(default=True)
  is_scorekeeper = db.BooleanProperty(default=False)

  @staticmethod
  def ordered():
    r = Competitor.all()
    r.filter("include_in_rankings =", True)
    r.order("-rating")
    return [c for c in r] 

  @staticmethod
  def by_id(id):
    r = Competitor.all()
    r.filter("userid =", id)
    return r.get()

class Result(db.Model):
  date_played = db.DateTimeProperty()
  winner_user_id = db.StringProperty()
  loser_user_id = db.StringProperty()
  winner_old_rating = db.FloatProperty()
  loser_old_rating = db.FloatProperty()
  winner_new_rating = db.FloatProperty()
  loser_new_rating = db.FloatProperty()
  winner_score = db.IntegerProperty()
  loser_score = db.IntegerProperty()

  def winner_name(self):
    c = Competitor.by_id(self.winner_user_id)
    return c.nickname

  def loser_name(self):
    c = Competitor.by_id(self.loser_user_id)
    return c.nickname

  def points_transacted(self):
    return self.winner_new_rating - self.winner_old_rating

  @staticmethod
  def all_results():
    q = Result.all()
    q.order('-date_played')
    q.get()
    return [c for c in q]
    
  @staticmethod
  def user_results(userid, won=True):
    q = Result.all()
    q.order('-date_played')
    if won:
      q.filter('winner_user_id =', userid)
    else:
      q.filter('loser_user_id =', userid)
    q.get()
    return [c for c in q]
  
  @staticmethod
  def all_for(userid):
    won = Result.user_results(userid, True)
    lost = Result.user_results(userid, False)
    return sorted(
        (won + lost), 
        key=operator.attrgetter('date_played'), 
        reverse=True)
    

  @staticmethod
  def process_match_result(winner, loser, winners_score, losers_score):
    logging.info("result: %s(%s) defeated %s(%s)" % (winner.nickname, winner.rating, loser.nickname, loser.rating))
        
    new_ratings = EloRating.calculate_elo_rank(winner.rating,loser.rating)

    logging.info("new ratings are:")
    logging.info("  %s - %s" % (winner.nickname, new_ratings[0]))
    logging.info("  %s - %s" % (loser.nickname, new_ratings[1]))

    res = Result(
        date_played = datetime.datetime.now(),
        winner_user_id = winner.userid,
        loser_user_id = loser.userid,
        winner_old_rating = winner.rating,
        loser_old_rating = loser.rating,
        winner_new_rating = new_ratings[0],
        loser_new_rating = new_ratings[1], 
        winner_score = winners_score,
        loser_score = losers_score
        )
    res.put()
    
    winner.rating = new_ratings[0]
    loser.rating = new_ratings[1]
    winner.put()
    loser.put()



#TODO _ penalise for non-play; reward for most play
class RatingAdjustment(db.Model):
  userid = db.StringProperty()
  date = db.DateTimeProperty()
  old_rating = db.FloatProperty()
  new_rating = db.FloatProperty()
  reason = db.StringProperty()


