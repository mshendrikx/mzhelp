import os
from dotenv import load_dotenv
from tasks import get_team_players_data

load_dotenv()

players = get_team_players_data(os.getenv("MZUSER"), os.getenv("MZPASS"))