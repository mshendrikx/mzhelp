from flask_login import UserMixin
from sqlalchemy.dialects.mysql import LONGTEXT
from . import db


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(100))
    password = db.Column(db.String(1000))
    admin = db.Column(db.String(1))
    mzuser = db.Column(db.String(100))
    mzpass = db.Column(db.String(1000))


class Player(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    number = db.Column(db.Integer)
    country = db.Column(db.Integer, nullable=False, index=True)
    age = db.Column(db.Integer)
    transferage = db.Column(db.Integer)
    season = db.Column(db.Integer)
    teamid = db.Column(db.Integer, nullable=False, index=True)
    national = db.Column(db.Integer)
    totalskill = db.Column(db.Integer)
    height = db.Column(db.Integer)
    weight = db.Column(db.Integer)
    foot = db.Column(db.Integer)
    starhigh = db.Column(db.Integer)
    starlow = db.Column(db.Integer)
    startraining = db.Column(db.Integer)
    value = db.Column(db.Integer)
    salary = db.Column(db.Integer)
    retiring = db.Column(db.Integer)
    speed = db.Column(db.Integer)
    speedmax = db.Column(db.Integer)
    speedscout = db.Column(db.Integer)
    stamina = db.Column(db.Integer)
    staminamax = db.Column(db.Integer)
    staminascout = db.Column(db.Integer)
    intelligence = db.Column(db.Integer)
    intelligencemax = db.Column(db.Integer)
    intelligencescout = db.Column(db.Integer)
    passing = db.Column(db.Integer)
    passingmax = db.Column(db.Integer)
    passingscout = db.Column(db.Integer)
    shooting = db.Column(db.Integer)
    shootingmax = db.Column(db.Integer)
    shootingscout = db.Column(db.Integer)
    heading = db.Column(db.Integer)
    headingmax = db.Column(db.Integer)
    headingscout = db.Column(db.Integer)
    keeping = db.Column(db.Integer)
    keepingmax = db.Column(db.Integer)
    keepingscout = db.Column(db.Integer)
    control = db.Column(db.Integer)
    controlmax = db.Column(db.Integer)
    controlscout = db.Column(db.Integer)
    tackling = db.Column(db.Integer)
    tacklingmax = db.Column(db.Integer)
    tacklingscout = db.Column(db.Integer)
    aerial = db.Column(db.Integer)
    aerialmax = db.Column(db.Integer)
    aerialscout = db.Column(db.Integer)
    plays = db.Column(db.Integer)
    playsmax = db.Column(db.Integer)
    playsscout = db.Column(db.Integer)
    experience = db.Column(db.Integer)
    form = db.Column(db.Integer)
    traininginfo = db.Column(db.Integer)
    changedat = db.Column(db.BigInteger)


class PlayerTraining(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    trainingdate = db.Column(db.BigInteger)
    trainingdata = db.Column(LONGTEXT, nullable=True)


class Mzcontrol(db.Model):
    id = db.Column(db.String(100), primary_key=True)
    season = db.Column(db.Integer)
    deadline = db.Column(db.BigInteger)


class Countries(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    flag = db.Column(db.String(1024))
    ages = db.Column(db.Integer)


class Tranfers(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    playerid = db.Column(db.Integer, nullable=False, index=True)
    deadline = db.Column(db.BigInteger, nullable=False, index=True)
    askingprice = db.Column(db.Integer)
    actualprice = db.Column(db.Integer)


class Bids(db.Model):
    userid = db.Column(db.Integer, primary_key=True)
    transferid = db.Column(db.Integer, primary_key=True)
    maxbid = db.Column(db.Integer)
    finalvalue = db.Column(db.Integer)
    active = db.Column(db.Integer)
