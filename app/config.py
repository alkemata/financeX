import os
from dotenv import load_dotenv
from datetime import timedelta

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'supersecretkey'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:////app/users.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    PERMANENT_SESSION_LIFETIME = timedelta(hours=1)

    def __init__(self, config_file_path='./FinanceX/resources/variables.txt'):
        self.config_dict = {}
        with open(config_file_path, 'r') as file:
            for line in file:
                line = line.strip()
                if not line:
                    continue
                if '=' in line:
                    key, value = line.split('=', 1)
                    self.config_dict[key.strip()] = value.strip()

    def get(self, key):
        return self.config_dict.get(key)