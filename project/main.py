
from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash
from . import db

from .common import utc_input, countries_data
from .models import Tranfers, Player

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
    
    utc_now = utc_input()
    countries = countries_data(index=0)
    transfers = []    
    db_transfers = Tranfers.query.filter(Tranfers.deadline >= utc_now, Tranfers.active == 1).order_by(Tranfers.deadline).all()
    count = 0
    for db_transfer in db_transfers:
        player = Player.query.filter_by(id=db_transfer.playerid).first()
        if player:
            transfer = []
            transfer.append(db_transfer)
            transfer.append(player)
            transfer.append(countries[player.country])
            transfers.append(transfer)
            count += 1
        if count == 5:
            break
               
    return render_template("transfers.html", current_user=current_user, transfers=transfers)

@main.route("/transfers", methods=["POST"])
@login_required
def transfers_post():
    1 == 1