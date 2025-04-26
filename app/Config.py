import os
from dotenv import load_dotenv

# Load .env file
load_dotenv()

class Config:
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    SQL_SERVER = os.getenv("SQL_SERVER")
    SQL_DATABASE = os.getenv("SQL_DATABASE")
    SQL_DRIVER = os.getenv("SQL_DRIVER", "ODBC Driver 17 for SQL Server")