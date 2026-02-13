import os
import logging
import mysql.connector

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from werkzeug.security import generate_password_hash
from flask_apscheduler import APScheduler

# from .jobs import job_control

# init SQLAlchemy so we can use it later in our models
db = SQLAlchemy()
scheduler = APScheduler()

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)

# Add logging to debug
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_app():

    app = Flask(__name__)

    mariadb_pass = os.environ.get("MZDBPASS")
    mariadb_host = os.environ.get("MZDBHOST")
    mariadb_port = os.environ.get("MZDBPORT")
    mariadb_database = os.environ.get("MZDBNAME")

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

    app.config["SCHEDULER_API_ENABLED"] = True
    app.config["SCHEDULER_TIMEZONE"] = "America/Sao_Paulo"
    app.config["SCHEDULER_JOBSTORES"] = {
        "default": {
            "type": "sqlalchemy",
            "url": app.config["SQLALCHEMY_DATABASE_URI"],
        }
    }

    
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
            Users,
            Players,
            PlayersTraining,
            Mzcontrol,
            Countries,
            Transfers,
            Bids,
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
        user = Users.query.filter_by(id=1).first()
        if not user:
            new_user = Users(
                id = 1,
                email=os.environ.get("ADMEMAIL"),
                name=os.environ.get("ADMNAME"),
                password=generate_password_hash(
                    os.environ.get("ADMPASS"), method="pbkdf2:sha256"
                ),
                admin=1,
                mzuser=os.environ.get("MZUSER"),
                mzpass=os.environ.get("MZPASS"),
            )
            db.session.add(new_user)
            db.session.commit()
    
        from project.jobs import job_control, job_teams, job_transfers, job_nations

        jobs = scheduler.get_jobs()  # Load jobs from the database
        
        if not jobs:
            # Control Job
            job_func = job_control
            scheduler.add_job(
                id='job_control',
                func=job_func,
                trigger='cron',
                minute='0',
                hour='0',
                day='*',
                month='*',
                day_of_week='*',                
                max_instances=1,
            )
            
            job_func = job_teams
            scheduler.add_job(
                id='job_teams',
                func=job_func,
                trigger='cron',
                minute='0',
                hour='2',
                day='*',
                month='*',
                day_of_week='*',                            
                max_instances=1,
            )
            
            job_func = job_transfers
            scheduler.add_job(
                id='job_transfers',
                func=job_func,
                trigger='cron',
                minute='0',
                hour='4,16',
                day='*',
                month='*',
                day_of_week='*',                            
                max_instances=1,
            )
            
            job_func = job_nations
            scheduler.add_job(
                id='job_nations',
                func=job_func,
                trigger='cron',
                minute='30',
                hour='0',
                day='*',
                month='*',
                day_of_week='*',                            
                max_instances=1,
            )

        
    @login_manager.user_loader
    def load_user(userid):
        # since the user_id is just the primary key of our user table, use it in the query for the user
        return Users.query.get(userid)

    # blueprint for auth routes in our app
    from .auth import auth as auth_blueprint

    app.register_blueprint(auth_blueprint)

    # blueprint for non-auth parts of app
    from .main import main as main_blueprint

    app.register_blueprint(main_blueprint)

    return app
