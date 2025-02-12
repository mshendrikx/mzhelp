import os

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from werkzeug.security import generate_password_hash
from apscheduler.schedulers.background import BackgroundScheduler


# init SQLAlchemy so we can use it later in our models
db = SQLAlchemy()

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)


def create_app():

    app = Flask(__name__)

    mariadb_pass = os.environ.get("MZDBPASS")
    mariadb_host = os.environ.get("MZDBHOST")
    mariadb_database = os.environ.get("MZDBNAME")

    app = Flask(__name__)

    app.config["SECRET_KEY"] = os.urandom(24).hex()
    app.config["SQLALCHEMY_DATABASE_URI"] = (
        "mysql+pymysql://root:"
        + mariadb_pass
        + "@"
        + mariadb_host
        + "/"
        + mariadb_database
    )

    db.init_app(app)

    scheduler = BackgroundScheduler()

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

        # add admin user to the database
        user = User.query.filter_by(id=1).first()
        if not user:
            new_user = User(
                id=1,
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

    app.scheduler = scheduler

    return app
