import os
from dotenv import load_dotenv

os.environ["RUN_TIMEZONE_CHECK"] = "0"

from db import init_db

load_dotenv()

if __name__ == "__main__":
    print("Initializing database...")
    init_db(force_reset=False) # use force_reinit=True to reset tables
    print(" Database initialization finished.")
