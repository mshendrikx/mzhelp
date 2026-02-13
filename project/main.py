
from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash
from . import db
from . import scheduler

from .common import utc_input, countries_data
from .models import Tranfers, Player, Jobs

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
    
    jobs = Jobs.query.all()
    
    for job in jobs:
        if job.id == 'job_control':
            job_control = job
        if job.id == 'job_teams':
            job_teams = job
        if job.id == 'job_transfers':
            job_transfers = job
        if job.id == 'job_nations':
            job_nations = job

    return render_template("configuration.html", current_user=current_user, job_control=job_control, job_teams=job_teams, job_transfers=job_transfers, job_nations=job_nations)

@main.route("/update_jobs", methods=["POST"])
@login_required
def update_jobs():

    jobs = Jobs.query.all()

    for job in jobs:
        if job.id == 'job_control':
            job_control = job
            job_control.minute = request.form.get(f"control_minute")
            job_control.hour = request.form.get(f"control_hour")
            job_control.day = request.form.get(f"control_day")
            job_control.month = request.form.get(f"control_month")
            job_control.weekday = request.form.get(f"control_weekday")
            if request.form.get("control_enabled"):
                job_control.enabled = 1
            else:
                job_control.enabled = 0
            db.session.add(job_control)
            
        if job.id == 'job_teams':
            job_teams = job
            job_teams.minute = request.form.get(f"teams_minute")
            job_teams.hour = request.form.get(f"teams_hour")
            job_teams.day = request.form.get(f"teams_day")
            job_teams.month = request.form.get(f"teams_month")
            job_teams.weekday = request.form.get(f"teams_weekday")
            if request.form.get("teams_enabled"):
                job_teams.enabled = 1
            else:
                job_teams.enabled = 0
            db.session.add(job_teams)
            
        if job.id == 'job_transfers':
            job_transfers = job
            job_transfers.minute = request.form.get(f"transfers_minute")
            job_transfers.hour = request.form.get(f"transfers_hour")
            job_transfers.day = request.form.get(f"transfers_day")
            job_transfers.month = request.form.get(f"transfers_month")
            job_transfers.weekday = request.form.get(f"transfers_weekday")
            if request.form.get("transfers_enabled"):
                job_transfers.enabled = 1
            else:
                job_transfers.enabled = 0
            db.session.add(job_transfers)

        if job.id == 'job_nations':
            job_nations = job
            job_nations.minute = request.form.get(f"nations_minute")
            job_nations.hour = request.form.get(f"nations_hour")
            job_nations.day = request.form.get(f"nations_day")
            job_nations.month = request.form.get(f"nations_month")
            job_nations.weekday = request.form.get(f"nations_weekday")
            if request.form.get("nations_enabled"):
                job_nations.enabled = 1
            else:
                job_nations.enabled = 0
            db.session.add(job_nations)
    
    
    
    

    db.session.commit()

    return redirect(url_for("main.configuration"))

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