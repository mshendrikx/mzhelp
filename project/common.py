import os
import smtplib
import json

from datetime import datetime, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from .models import User, Mzcontrol, Player, Countries
from sqlalchemy import create_engine

# from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import scoped_session, sessionmaker
from datetime import datetime
from bs4 import BeautifulSoup

from . import db

FIRST_DAY = datetime.strptime("2002-01-29", "%Y-%m-%d").date()


def get_db():

    mariadb_pass = os.environ.get("MZDBPASS")
    mariadb_host = os.environ.get("MZDBHOST")
    mariadb_database = os.environ.get("MZDBNAME")

    sql_text = (
        "mysql+pymysql://root:"
        + mariadb_pass
        + "@"
        + mariadb_host
        + "/"
        + mariadb_database
    )

    # Create the SQLAlchemy engine
    engine = create_engine(sql_text)

    # Create a session factory
    session_factory = sessionmaker(bind=engine)
    Session = scoped_session(session_factory)

    # Bind the Flask-SQLAlchemy models to the new engine
    db.Model.metadata.bind = engine
    session = Session()

    return session


def only_numerics(seq):
    seq_type = type(seq)
    return seq_type().join(filter(seq_type.isdigit, seq))


def countries_data(index=0):

    # index=0: Indexed by id
    # index=1: Indexed by name

    session = get_db()
    countries = session.query(Countries).all()
    countries_list = {}
    for country in countries:
        if index == 0:
            countries_list[country.id] = country
        elif index == 1:
            countries_list[country.name] = country

    return countries_list


def get_utc_string(format="%Y-%m-%d %H:%M:%S"):

    # Get the current UTC time
    utc_now = datetime.now(timezone.utc)
    return utc_now.strftime(format)


def get_mz_day(date=""):

    if date == "":
        date_dt = datetime.strptime(
            get_utc_string(format="%Y-%m-%d"), "%Y-%m-%d"
        ).date()
    else:
        date_dt = datetime.strptime(date, "%Y-%m-%d").date()

    dif_days = date_dt - FIRST_DAY
    dif_days = dif_days.days

    year, day = divmod(dif_days, 91)
    year += 1
    day += 1

    return str(year) + "-" + str(day)


def set_player_scout(scout_page, player):

    soup = BeautifulSoup(scout_page, "lxml")
    scouts_dd = soup.find_all("dd")
    count = 0
    for scout_dd in scouts_dd:
        stars = len(scout_dd.find_all(class_="fa fa-star fa-2x lit"))
        if count != 2:
            if count == 0:
                player.starhigh = stars
            else:
                player.starlow = stars
            if "Speed" in scout_dd.text:
                player.speedscout = stars
            if "Stamina" in scout_dd.text:
                player.staminascout = stars
            if "Intelligence" in scout_dd.text:
                player.intelligencescout = stars
            if "Passing" in scout_dd.text:
                player.passingscout = stars
            if "Shooting" in scout_dd.text:
                player.shootingscout = stars
            if "Heading" in scout_dd.text:
                player.headingscout = stars
            if "Keeping" in scout_dd.text:
                player.keepingscout = stars
            if "Control" in scout_dd.text:
                player.controlscout = stars
            if "Tackling" in scout_dd.text:
                player.tacklingscout = stars
            if "Aerial" in scout_dd.text:
                player.aerialscout = stars
            if "Plays" in scout_dd.text:
                player.playsscout = stars
        else:
            player.startraining = stars
        count += 1

    return player


def format_training_data(trainig_page):

    soup_data = BeautifulSoup(trainig_page, "lxml")
    text = soup_data.html.body.text
    text = text.split("var series = ")[1]
    text = text.split("}}]}]")[0] + "}}]}]"

    json_data = json.loads(text)
    index = len(json_data) - 1
    json_string = json.dumps(json_data[index]["data"])

    return json_string


def recover_email(user, password):

    # Usage with a custom sender name
    sender_name = "MZApp"
    sender_email = os.environ["MZAPP_EMAIL"]
    recipient_email = user.email
    subject = "MZApp Login"
    text_content = "User: " + str(user.email) + "\n" + "Password: " + str(password)

    return send_email(
        sender_name=sender_name,
        sender_email=sender_email,
        recipient=recipient_email,
        subject=subject,
        text_content=text_content,
        smtp_server=os.environ["SMTP_SERVER"],
        smtp_port=os.environ["SMTP_PORT"],
    )


def send_email(
    sender_name,
    sender_email,
    recipient,
    subject,
    text_content,
    html_content=None,
    smtp_server="localhost",
    smtp_port=25,
):
    message = create_message(
        sender_name, sender_email, recipient, subject, text_content, html_content
    )

    try:
        # Connect to the SMTP server (modify server/port as needed)
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            # Start TLS encryption if required by Postfix configuration
            if server.has_extn("STARTTLS"):
                server.starttls()

            # Authenticate if required (check Postfix configuration)
            if server.has_extn("AUTH"):
                # Replace with your credentials
                server.login("your_username", "your_password")

            server.sendmail(sender_email, recipient, message.as_string())

            return True
    except:
        return False


def create_message(
    sender_name, sender_email, recipient, subject, text_content, html_content=None
):
    message = MIMEMultipart("alternative")
    message["From"] = (
        sender_name + " <" + sender_email + ">"
    )  # Set sender name and email
    message["To"] = recipient
    message["Subject"] = subject

    # Add plain text part
    part1 = MIMEText(text_content, "plain")
    message.attach(part1)

    # Add HTML part (optional)
    if html_content:
        part2 = MIMEText(html_content, "html")
        message.attach(part2)

    return message
