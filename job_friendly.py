import os
import logging

from datetime import datetime
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

logging.info("Starting the script")

users = session.query(Users).all()

for user in users:
    if user.countryid == 0:
        logging.info(f"Skipping user {user.mzuser} with countryid 0")
        continue
    logging.info(f"Processing user: {user.mzuser}")
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
            sb.open("https://www.managerzone.com/?p=challenges&tab=quick")

            sb.wait_for_element_visible('a[id="qc-countdown-wrapper"]', timeout=10)

            weekday = datetime.now().weekday()

            if weekday == 0:
                home_tactic = user.hometue
                away_tactic = user.awaytue
            elif weekday == 1:
                home_tactic = None
                away_tactic = None
            elif weekday == 2:
                home_tactic = user.homethu
                away_tactic = user.awaythu
            elif weekday == 3:
                home_tactic = user.homefri
                away_tactic = user.awayfri
            elif weekday == 4:
                home_tactic = user.homesat
                away_tactic = user.awaysat
            elif weekday == 5:
                home_tactic = None
                away_tactic = None
            elif weekday == 6:
                home_tactic = user.homemon
                away_tactic = user.awaymon

            logging.info(f"Home tactic: {home_tactic}, Away tactic: {away_tactic}")

            if home_tactic is not None and away_tactic is not None:
            
                sb.select_option_by_value("#tactic_home", home_tactic)
                sb.select_option_by_value("#tactic_away", away_tactic)

                sb.click('a[id="qc-opt-in"]')
                
        except Exception as e:
            logging.error(f"An error occurred for user {user.mzuser}: {str(e)}")

logging.info("Finishing the script")