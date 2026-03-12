import os
import logging

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from seleniumbase import SB
from pathlib import Path
from bs4 import BeautifulSoup
from project.models import Users
from project.common import (
    get_db,
    only_numerics,
    countries_data,
    get_utc_string,
    get_mz_day,
    process_training_data,
    utc_input,
)

from dotenv import load_dotenv

load_dotenv()

session = get_db()

utc_string = get_utc_string(format="%Y%m%d%H%M")
log_file_name = "job_team_" + utc_string + ".log"

# Get the directory of the script
script_dir = Path(__file__).parent
# Define the logs directory (same level as the script)
logs_dir = script_dir / "logs"
# Create the logs directory if it doesn't exist
logs_dir.mkdir(exist_ok=True)
# Configure logging to save logs in the logs folder
log_file = logs_dir / log_file_name  # Path to the log file
logging.basicConfig(
    level=logging.INFO,  # Set the logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",  # Define the log format
    filename=str(log_file),  # Optional: Log to a file instead of the console
    filemode="a",  # Optional: 'a' for append, 'w' for overwrite
)

logging.info("Starting the event script")

users = session.query(Users).all()

for user in users:
    if user.countryid == 0:
        logging.info(f"Skipping user {user.mzuser} event with countryid 0")
        continue
    
    int_utc_now = int(datetime.now().astimezone(ZoneInfo("UTC")).strftime("%Y%m%d%H%M"))
    
#    if user.nextclaim > int_utc_now:
#        logging.info(f"Skipping user {user.mzuser} event with nextclaim in the future")
#        continue
    
    logging.info(f"Processing event user: {user.mzuser}")
    with SB(
        headless=True,
        #browser="firefox",
        uc=True,
        servername=os.environ.get("SELENIUM_HUB_HOST"),
        port=os.environ.get("SELENIUM_HUB_PORT"),
    ) as sb:
        
        try:
        
            logging.info("Login to ManagerZone")
            sb.open("https://www.managerzone.com/")
            sb.click('button[id="CybotCookiebotDialogBodyLevelButtonLevelOptinAllowAll"]')
            sb.type('input[id="login_username"]', user.mzuser)
            sb.type('input[id="login_password"]', user.mzpass)
            sb.click('a[id="login"]')
            sb.open("https://www.managerzone.com/?p=event")
#            sb.wait_for_element_visible('//*[@id="claim"]', timeout=10)            
#            sb.click('a[id="claim"]')
#            sb.open("https://www.managerzone.com/?p=event")
            sb.wait_for_element_visible('//*[@id="next-reset-clock"]', timeout=10)
            clock_string = sb.get_text('//*[@id="next-reset-clock"]')
            clock_parts = clock_string.split(" ")
            hours = int(only_numerics(clock_parts[0]))
            minutes = int(only_numerics(clock_parts[1])) + 1          
            
            next_claim_date = datetime.now().astimezone(ZoneInfo("UTC")) + timedelta(hours=hours, minutes=minutes)
            
            user.nextclaim = int(next_claim_date.strftime("%Y%m%d%H%M"))
            session.commit()
                
        except Exception as e:
            logging.error(f"An error occurred for for claim event for user {user.mzuser}: {str(e)}")

logging.info("Finishing the event script")