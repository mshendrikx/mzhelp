
from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash
from . import db

main = Blueprint("main", __name__)

@main.route("/")
def index():

    return render_template("index.html", user=current_user)

@main.route("/profile")
@login_required
def profile():

    return render_template("profile.html", current_user=current_user)


@main.route("/profile", methods=["POST"])
@login_required
def profile_post():

    password = request.form.get("password")
    repass = request.form.get("repass")
    name = request.form.get("name")
    email = request.form.get("email")

    if password != repass:
        flash("Password está diferente")
        flash("alert-danger")
        return redirect(url_for("main.profile"))

    if '@' not in email:
        flash("Entrar E-mail válido")
        flash("alert-danger")
        return redirect(url_for("main.profile"))
            
    if password != "":
        current_user.password = generate_password_hash(password, method="pbkdf2:sha256")

    if name != "":
        current_user.name = name
        
    current_user.email = email

    db.session.add(current_user)
    db.session.commit()

    return redirect(url_for("main.profile"))

@main.route("/configuration")
@login_required
def configuration():

    return render_template("configuration.html", current_user=current_user)

@main.route("/transfers")
@login_required
def transfers():
    1 == 1

@main.route("/transfers", methods=["POST"])
@login_required
def transfers_post():
    1 == 1