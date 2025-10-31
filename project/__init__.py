import os
import logging
import mysql.connector

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from werkzeug.security import generate_password_hash
from flask_apscheduler import APScheduler
from apscheduler.triggers.cron import CronTrigger

# from .jobs import job_control

# init SQLAlchemy so we can use it later in our models
db = SQLAlchemy()
scheduler = APScheduler()

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)


def create_app():

    app = Flask(__name__)

    mariadb_pass = os.environ.get("MZDBPASS")
    mariadb_host = os.environ.get("MZDBHOST")
    mariadb_port = os.environ.get("MZDBPORT")
    mariadb_database = os.environ.get("MZDBNAME")

    app = Flask(__name__)

    app.config["SCHEDULER_API_ENABLED"] = False
    app.config["SCHEDULER_TIMEZONE"] = "UTC"
    app.config["SECRET_KEY"] = os.urandom(24).hex()
    app.config["SQLALCHEMY_DATABASE_URI"] = (
        "mysql+pymysql://root:"
        + mariadb_pass
        + "@"
        + mariadb_host
        + ":"
        + mariadb_port
        + "/"
        + mariadb_database
    )
    
    try:
        conn = mysql.connector.connect(
            host=mariadb_host,
            port=mariadb_port,
            user='root',
            password=mariadb_pass
        )
        
        cursor = conn.cursor()
        
        # Create database if it doesn't exist
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {mariadb_database}")
        print(f"Database '{mariadb_database}' created successfully (or already exists)")
        
        # Switch to the database
        cursor.execute(f"USE {mariadb_database}")
        
        conn.commit()
        cursor.close()
        conn.close()

    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return False
    
    db.init_app(app)
    scheduler.init_app(app)
    scheduler.start()
    
    login_manager = LoginManager()
    login_manager.login_view = "auth.login"
    login_manager.init_app(app)

    with app.app_context():

        # Create tables
        from .models import (
            User,
            Player,
            PlayerTraining,
            Mzcontrol,
            Countries,
            Tranfers,
            Bids,
            Jobs,
        )

        db.create_all()
        db.session.commit()

        mzcontrol = Mzcontrol.query.first()

        if not mzcontrol:
            new_mzcontrol = Mzcontrol(
                id="MZCONTROL",
                season=0,
                deadline=0,
            )
            db.session.add(new_mzcontrol)
            db.session.commit()

        # add admin user to the database
        user = User.query.filter_by(id=1).first()
        if not user:
            new_user = User(
                id = 1,
                email=os.environ.get("ADMEMAIL"),
                name=os.environ.get("ADMNAME"),
                password=generate_password_hash(
                    os.environ.get("ADMPASS"), method="pbkdf2:sha256"
                ),
                admin="X",
                mzuser=os.environ.get("MZUSER"),
                mzpass=os.environ.get("MZPASS"),
            )
            db.session.add(new_user)
            db.session.commit()
    
        from project.jobs import job_control, job_teams, job_transfers

        # Add logging to debug
        logging.basicConfig(level=logging.INFO)
        logger = logging.getLogger(__name__)

        jobs = Jobs.query.all()
        for job in jobs:
            if job.enabled == 1:
                job_func = None
                if job.id == 'job_control':
                    job_func = job_control
                if job.id == 'job_teams':
                    job_func = job_teams
                if job.id == 'job_transfers':
                    job_func = job_transfers
                if job_func:
                    scheduler.add_job(
                        id=job.id,
                        func=job_func,
                        trigger=CronTrigger(
                            minute=job.minute,
                            hour=job.hour,
                            day=job.day,
                            month=job.month,
                            day_of_week=job.weekday,
                        ),
                        max_instances=1,
                    )
                else:
                    logger.warning(f"Job function for {job.id} not found")

    @login_manager.user_loader
    def load_user(userid):
        # since the user_id is just the primary key of our user table, use it in the query for the user
        return User.query.get(userid)

    # blueprint for auth routes in our app
    from .auth import auth as auth_blueprint

    app.register_blueprint(auth_blueprint)

    # blueprint for non-auth parts of app
    from .main import main as main_blueprint

    app.register_blueprint(main_blueprint)

    return app
