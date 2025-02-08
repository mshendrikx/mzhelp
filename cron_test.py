import logging
import os

from seleniumbase import SB
from pathlib import Path

log_file_name = "cron_test.log"
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

logging.info("Start Cron Test")

try:
    with SB(
        headless=True,
        #uc=True,
        servername=os.environ.get("SELENIUM_HUB_HOST"),
        port=os.environ.get("SELENIUM_HUB_PORT"),
    ) as sb:
        sb.open("https://www.managerzone.com/")
except Exception as e:
    logging.error(f"Error opening ManagerZone: {e}")
    raise

logging.info("Finish Cron Test")