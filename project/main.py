from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash
from project.common import get_db

from . import db
from . import scheduler

from .common import utc_input, countries_data
from .models import Transfers, Players, Countries


class Jobs:
    id = ""
    minute = ""
    hour = ""
    day = ""
    month = ""
    weekday = ""
    enabled = 0


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

    if "@" not in email:
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

    jobs = scheduler.get_jobs()

    for job in jobs:
        if job and hasattr(job.trigger, "fields"):
            f = {field.name: str(field) for field in job.trigger.fields}
            minute = f.get("minute")
            hour = f.get("hour")
            day = f.get("day")
            month = f.get("month")
            day_of_week = f.get("day_of_week")
            enabled = job.next_run_time
            if job.id == "job_control":
                job_control = Jobs()
                job_control.id = job.id
                job_control.minute = minute
                job_control.hour = hour
                job_control.day = day
                job_control.month = month
                job_control.weekday = day_of_week
                job_control.enabled = 1 if enabled else 0
            if job.id == "job_teams":
                job_teams = Jobs()
                job_teams.id = job.id
                job_teams.minute = minute
                job_teams.hour = hour
                job_teams.day = day
                job_teams.month = month
                job_teams.weekday = day_of_week
                job_teams.enabled = 1 if enabled else 0
            if job.id == "job_transfers":
                job_transfers = Jobs()
                job_transfers.id = job.id
                job_transfers.minute = minute
                job_transfers.hour = hour
                job_transfers.day = day
                job_transfers.month = month
                job_transfers.weekday = day_of_week
                job_transfers.enabled = 1 if enabled else 0
            if job.id == "job_nations":
                job_nations = Jobs()
                job_nations.id = job.id
                job_nations.minute = minute
                job_nations.hour = hour
                job_nations.day = day
                job_nations.month = month
                job_nations.weekday = day_of_week
                job_nations.enabled = 1 if enabled else 0

    return render_template(
        "configuration.html",
        current_user=current_user,
        job_control=job_control,
        job_teams=job_teams,
        job_transfers=job_transfers,
        job_nations=job_nations,
    )


@main.route("/update_jobs", methods=["POST"])
@login_required
def update_jobs():

    # Control Job
    scheduler.modify_job(
        id="job_control",
        trigger="cron",
        minute=request.form.get(f"control_minute"),
        hour=request.form.get(f"control_hour"),
        day=request.form.get(f"control_day"),
        month=request.form.get(f"control_month"),
        day_of_week=request.form.get(f"control_weekday"),
        max_instances=1,
    )
    if request.form.get("control_enabled"):
        scheduler.resume_job("job_control")
    else:
        scheduler.pause_job("job_control")

    # Teams Job
    scheduler.modify_job(
        id="job_teams",
        trigger="cron",
        minute=request.form.get(f"teams_minute"),
        hour=request.form.get(f"teams_hour"),
        day=request.form.get(f"teams_day"),
        month=request.form.get(f"teams_month"),
        day_of_week=request.form.get(f"teams_weekday"),
        max_instances=1,
    )
    if request.form.get("teams_enabled"):
        scheduler.resume_job("job_teams")
    else:
        scheduler.pause_job("job_teams")

    # Transfers Job
    scheduler.modify_job(
        id="job_transfers",
        trigger="cron",
        minute=request.form.get(f"transfers_minute"),
        hour=request.form.get(f"transfers_hour"),
        day=request.form.get(f"transfers_day"),
        month=request.form.get(f"transfers_month"),
        day_of_week=request.form.get(f"transfers_weekday"),
        max_instances=1,
    )
    if request.form.get("transfers_enabled"):
        scheduler.resume_job("job_transfers")
    else:
        scheduler.pause_job("job_transfers")

    # Nations Job
    scheduler.modify_job(
        id="job_nations",
        trigger="cron",
        minute=request.form.get(f"nations_minute"),
        hour=request.form.get(f"nations_hour"),
        day=request.form.get(f"nations_day"),
        month=request.form.get(f"nations_month"),
        day_of_week=request.form.get(f"nations_weekday"),
        max_instances=1,
    )
    if request.form.get("nations_enabled"):
        scheduler.resume_job("job_nations")
    else:
        scheduler.pause_job("job_nations")

    return redirect(url_for("main.configuration"))


@main.route("/transfers")
@login_required
def transfers():

    transfers = []
    countries = Countries.query.order_by(Countries.name).all()

    return render_template(
        "transfers.html",
        current_user=current_user,
        countries=countries,
        transfers=transfers,
    )


@main.route("/transfers", methods=["POST"])
@login_required
def transfers_post():

    session = get_db()
    utc_now = utc_input()
    session.query(Transfers).filter(
        Transfers.deadline < utc_now, Transfers.active == 1
    ).update({"active": 0})
    session.commit()

    utc_now = utc_input()
    countries = countries_data(index=0)
    transfers = []
    db_transfers = (
        Transfers.query.filter(Transfers.deadline >= utc_now, Transfers.active == 1)
        .order_by(Transfers.deadline)
        .all()
    )
    count = 0
    for db_transfer in db_transfers:
        player = Players.query.filter_by(id=db_transfer.playerid).first()
        if player:
            transfer = []
            transfer.append(db_transfer)
            transfer.append(player)
            transfer.append(countries[player.country])
            transfers.append(transfer)
            count += 1
        if count == 5:
            break
    return render_template(
        "transfers.html", current_user=current_user, transfers=transfers
    )
