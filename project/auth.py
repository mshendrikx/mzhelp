import os

from flask import Blueprint, render_template, redirect, url_for, request, flash
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, login_required, logout_user
from .models import User
from .common import recover_email
from . import db

auth = Blueprint("auth", __name__)

@auth.route("/login")
def login():
    return render_template("login.html")

@auth.route("/login", methods=["POST"])
def login_post():
    # login code goes here
    email = request.form.get("email")
    password = request.form.get("password")
    remember = True if request.form.get("remember") else False

    user = User.query.filter_by(email=email).first()
    # check if the user actually exists
    # take the user-supplied password, hash it, and compare it to the hashed password in the database
    if not user or not check_password_hash(user.password, password):
        flash("Check data and try again.")
        flash("alert-danger")
        return redirect(
            url_for("auth.login")
        )  # if the user doesn't exist or password is wrong, reload the page
    
    login_user(user, remember=remember)
    db.session.add(user)
    db.session.commit()

    return redirect(url_for("main.profile"))

@auth.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("main.index"))

@auth.route("/recoverlogin")
def recoverlogin():

    return render_template("recoverlogin.html")

@auth.route("/recoverlogin", methods=["POST"])
def recoverlogin_post():

    email = request.form.get("email")
    
    if "@" not in email:
        flash("It's not valid E-mail")
        flash("alert-danger")
        return redirect(url_for("auth.recoverlogin"))

    user = User.query.filter_by(
        email=email
    ).first()  

    if ( not user ):  
        flash("E-mail do not exist in database.")
        flash("alert-danger")
    else:
        password = os.urandom(5).hex()
        if recover_email(user, password):
            user.password = generate_password_hash(password, method="pbkdf2:sha256")
            db.session.commit()
            flash("Recover E-mail sended.")
            flash("alert-success")
        else:     
            flash("Fali to send recover email. Contact administrator.")
            flash("alert-danger")

    return redirect(url_for("auth.login"))