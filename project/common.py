
import os
import smtplib

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from .models import User, Updates, Mzcontrol, Player, Countries
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import  scoped_session, sessionmaker

from . import db

def get_db():
    
    mariadb_pass = os.environ.get("MZDBPASS")
    mariadb_host = os.environ.get("MZDBHOST")
    mariadb_database = os.environ.get("MZDBNAME")
    
    sql_text = "mysql+pymysql://root:" + mariadb_pass + "@" + mariadb_host + "/" + mariadb_database
    
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
    seq_type= type(seq)
    return seq_type().join(filter(seq_type.isdigit, seq))

def countries_data(index=0):

    #index=0: Indexed by id
    #index=1: Indexed by name    

    session = get_db()
    countries = session.query(Countries).all()
    countries_list = {}
    for country in countries:
        if index == 0:
            countries_list[country.id] = country
        elif index == 1:
            countries_list[country.name] = country
            
    return countries_list            
    
def recover_email(user, password):

    # Example usage with a custom sender name
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

