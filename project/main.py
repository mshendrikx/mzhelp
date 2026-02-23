import os

from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash
from sqlalchemy import inspect, text
from datetime import datetime, timedelta
from seleniumbase import SB

from . import db
from . import scheduler
from . import logger

from project.common import get_db
from project.jobs import job_bid
from .common import utc_input, countries_data
from .models import Transfers, Players, Countries, Bids


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
    mzuser = request.form.get("mzuser")
    mzpass = request.form.get("mzpass")

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
    
    with SB(
        headless=True,
        uc=True,
        servername=os.environ.get("SELENIUM_HUB_HOST", None),
            port=os.environ.get("SELENIUM_HUB_PORT", None),
    ) as sb:
        try:
            job_id = f"job_bid_{current_user.id}"  
            job_bid = scheduler.get_job(job_id)
            
            sb.open("https://www.managerzone.com/")
            sb.click('button[id="CybotCookiebotDialogBodyLevelButtonLevelOptinAllowAll"]')
            sb.type('input[id="login_username"]', mzuser)
            sb.type('input[id="login_password"]', mzpass)
            sb.click('a[id="login"]')     
            sb.wait_for_element('//*[@id="header-stats-wrapper"]/h5[3]')            
                      
            if job_bid:
                scheduler.resume_job(job_id)
            else:
                scheduler.add_job(
                    id=job_id,
                    func=job_bid,
                    trigger='cron',
                    minute='0,5,10,15,20,25,30,35,40,45,50,55',
                    hour='*',
                    day='*',
                    month='*',
                    day_of_week='*',                
                    max_instances=1,
                    args=[current_user.id]
                )
            current_user.mzuser = mzuser
            current_user.mzpass = mzpass
            
        except Exception as e:
            logger.error("Error logging in user with provided MZ credentials: " + str(current_user.id))
            logger.error(e)
            flash("Error logging in user with provided MZ credentials")
            flash("alert-danger")
            if job_bid:
                scheduler.pause_job(job_id)            


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

    countries = Countries.query.order_by(Countries.name).all()
    inspector = inspect(db.engine)
    view_names = inspector.get_view_names()
    views = []
    for view_name in view_names:
        if view_name.startswith("TR_"):
            views.append(view_name)

    countries_indexed = countries_data(index=0)

    utc_now = utc_input()
    Transfers.query.filter(Transfers.deadline < utc_now, Transfers.active == 1).update({"active": 0})
    transfers = []
    nationality = request.args.get("nationality")
    view = request.args.get("view")
    try:
        max_price = int(request.args.get("max_price", 0))
    except:
        max_price = 0
    active_bids = request.args.get("active_bids")
    
    if active_bids:
        db_bids = Bids.query.filter_by(active=1, userid=current_user.id).all()
        if not db_bids:
            flash("No active bids found")
            flash("alert-warning")
            return redirect(url_for("main.transfers"))

        for db_bid in db_bids:
            db_transfer = Transfers.query.filter_by(id=db_bid.transferid, active=1).first()
            if db_transfer:
                player = Players.query.filter_by(id=db_transfer.playerid).first()
                if player:
                    transfer = []
                    transfer.append(db_transfer)
                    transfer.append(player)
                    transfer.append(db_bid)
                    transfer.append(countries_indexed[player.country])
                    transfers.append(transfer)
            else:
                db_bid.active = 0
                db.session.commit()

    else:
        filters = [Transfers.active == 1]
        if max_price > 0:
            filters.append(Transfers.actualprice <= max_price)
            
        db_transfers = Transfers.query.filter(*filters).all()
        
        if not db_transfers:
            flash("No transfers found with the given filters")
            flash("alert-warning")
            return redirect(url_for("main.transfers"))
        
        players_id = []
        for db_transfer in db_transfers:
            players_id.append(db_transfer.playerid)            

        country_sel = current_user.countryid
                
        if nationality == "all_nationalities":
            query = text(f"SELECT * FROM {view} WHERE id IN :players_id AND country > :country")
            country_sel = 0
        elif nationality == "all_domestic":
            query = text(f"SELECT * FROM {view} WHERE id IN :players_id AND country = :country")
        elif nationality == "all_foreign":
            query = text(f"SELECT * FROM {view} WHERE id IN :players_id AND country != :country")
        else: 
            query = text(f"SELECT * FROM {view} WHERE id IN :players_id AND country = :country")
            try:
                country_sel = int(nationality)
            except:
                country_sel = 0

        try:
            result = db.session.execute(query, {"players_id": tuple(players_id), "country": country_sel})
            players_view = result.fetchall()
        except Exception as e:
            players_view = []
            
        view_ids = []
        for player_view in players_view:
            view_ids.append(player_view[0])
            
        db_transfers = Transfers.query.filter(Transfers.playerid.in_(view_ids), Transfers.active == 1).order_by(Transfers.deadline).all()
            
        for db_transfer in db_transfers:
            player = Players.query.filter_by(id=db_transfer.playerid).first()
            db_bid = Bids.query.filter_by(transferid=db_transfer.id, userid=current_user.id, active=1).first()
            if player:
                    transfer = []
                    transfer.append(db_transfer)
                    transfer.append(player)
                    if db_bid:
                        transfer.append(db_bid)
                    else:
                        transfer.append(None)
                    transfer.append(countries_indexed[player.country])
                    transfers.append(transfer)
    
    return render_template(
        "transfers.html",
        current_user=current_user,
        transfers=transfers,
        countries=countries,
        views=views,
    )

@main.route("/update_bid", methods=["POST"])
@login_required
def update_bid():
    transfer_id = request.form.get("transfer_id")
    max_bid = request.form.get("max_bid")
    
    if not transfer_id or not max_bid:
        flash("Invalid bid data")
        flash("alert-warning")
        # Preserve query parameters on error
        preserved_args = {}
        for key in ['search', 'nationality', 'view', 'max_price', 'active_bids']:
            value = request.form.get(f'query_{key}')
            if value:
                preserved_args[key] = value
        return redirect(url_for("main.transfers", **preserved_args))
    
    try:
        transfer_id = int(transfer_id)
        max_bid = int(max_bid)
    except ValueError:
        flash("Invalid bid values")
        flash("alert-warning")
        # Preserve query parameters on error
        preserved_args = {}
        for key in ['search', 'nationality', 'view', 'max_price', 'active_bids']:
            value = request.form.get(f'query_{key}')
            if value:
                preserved_args[key] = value
        return redirect(url_for("main.transfers", **preserved_args))
    
    # Check if transfer exists and is active
    transfer = Transfers.query.filter_by(id=transfer_id, active=1).first()
    if not transfer:
        flash("Transfer not found or inactive")
        flash("alert-warning")
        # Preserve query parameters on error
        preserved_args = {}
        for key in ['search', 'nationality', 'view', 'max_price', 'active_bids']:
            value = request.form.get(f'query_{key}')
            if value:
                preserved_args[key] = value
        return redirect(url_for("main.transfers", **preserved_args))
    
    # Validate bid amount - must be at least 5% higher than current price
    current_price = transfer.actualprice
    min_bid = int(current_price * 1.05)  # 5% higher than asking price
    
    if max_bid < min_bid:
        formatted_min_bid = "{:,}".format(min_bid).replace(",", ".")
        flash(f"Bid must be at least 5% higher than current price. Minimum bid: {formatted_min_bid} R$")
        flash("alert-warning")
        # Preserve query parameters on validation error
        preserved_args = {}
        for key in ['search', 'nationality', 'view', 'max_price', 'active_bids']:
            value = request.form.get(f'query_{key}')
            if value:
                preserved_args[key] = value
        return redirect(url_for("main.transfers", **preserved_args))
    
    # Check if bid already exists for this user and transfer
    existing_bid = Bids.query.filter_by(userid=current_user.id, transferid=transfer_id).first()
    
    if existing_bid:
        # Update existing bid
        existing_bid.maxbid = max_bid
        existing_bid.active = 1  # Reset final value
        db.session.commit()
        formatted_bid = "{:,}".format(max_bid).replace(",", ".")
        flash(f"Bid updated to {formatted_bid} R$")
    else:
        deadline_dt = datetime.strptime(str(transfer.deadline), "%Y%m%d%H%M")
        dtstart = deadline_dt - timedelta(minutes=20) 
        dtend = deadline_dt + timedelta(hours=23, minutes=59)
        # Create new bid
        new_bid = Bids(
            userid=current_user.id,
            transferid=transfer_id,
            maxbid=max_bid,
            finalvalue=0,
            dtstart=int(dtstart.strftime("%Y%m%d%H%M")),
            dtend=int(dtend.strftime("%Y%m%d%H%M")),
            active=1
        )
        db.session.add(new_bid)
        db.session.commit()
        formatted_bid = "{:,}".format(max_bid).replace(",", ".")
        flash(f"Bid placed: {formatted_bid} R$")
    
    flash("alert-success")
    
    # Preserve query parameters to maintain the same page state
    preserved_args = {}
    for key in ['search', 'nationality', 'view', 'max_price', 'active_bids']:
        value = request.form.get(f'query_{key}')
        if value:
            preserved_args[key] = value
    
    return redirect(url_for("main.transfers", **preserved_args))


@main.route("/clear_bid", methods=["POST"])
@login_required
def clear_bid():
    transfer_id = request.form.get("transfer_id")
    
    if not transfer_id:
        flash("Invalid transfer ID")
        flash("alert-warning")
        return redirect(url_for("main.transfers"))
    
    try:
        transfer_id = int(transfer_id)
    except ValueError:
        flash("Invalid transfer ID")
        flash("alert-warning")
        return redirect(url_for("main.transfers"))
    
    # Check if transfer exists and is active
    transfer = Transfers.query.filter_by(id=transfer_id, active=1).first()
    if not transfer:
        flash("Transfer not found or inactive")
        flash("alert-warning")
        return redirect(url_for("main.transfers"))
    
    # Check if bid exists for this user and transfer
    existing_bid = Bids.query.filter_by(userid=current_user.id, transferid=transfer_id, active=1).first()
    
    if existing_bid:
        # Deactivate the bid instead of deleting it
        existing_bid.active = 0
        db.session.commit()
        flash("Bid cleared successfully")
        flash("alert-success")
    else:
        flash("No active bid found for this transfer")
        flash("alert-warning")
    
    # Preserve query parameters to maintain the same page state
    preserved_args = {}
    for key in ['search', 'nationality', 'view', 'max_price', 'active_bids']:
        value = request.form.get(f'query_{key}')
        if value:
            preserved_args[key] = value
    
    return redirect(url_for("main.transfers", **preserved_args))
