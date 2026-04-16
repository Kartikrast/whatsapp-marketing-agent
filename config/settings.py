import os
from dotenv import load_dotenv

load_dotenv(override=True)

class Settings:
    APP_NAME = os.getenv("APP_NAME")
    APP_ENV = os.getenv("APP_ENV")
    WHATSAPP_API_TOKEN = os.getenv("WHATSAPP_API_TOKEN")
    WHATSAPP_PHONE_NUMBER_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID")
    WEBHOOK_VERIFY_TOKEN = os.getenv("WEBHOOK_VERIFY_TOKEN")
    WHATSAPP_API_URL = os.getenv("WHATSAPP_API_URL")
    # DATA_FILE_PATH = os.getenv("DATA_FILE_PATH")
    LANGGRAPH_API_URL = os.getenv("LANGGRAPH_API_URL")
    LANGSMITH_API_KEY = os.getenv("LANGSMITH_API_KEY")

settings = Settings()
