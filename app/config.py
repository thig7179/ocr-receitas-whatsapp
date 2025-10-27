import os
from dotenv import load_dotenv

# Carregar as variáveis do .env
load_dotenv()

TWILIO_SID = os.getenv("TWILIO_SID")
TWILIO_AUTH = os.getenv("TWILIO_AUTH")
AZURE_ENDPOINT = os.getenv("AZURE_ENDPOINT")
AZURE_KEY = os.getenv("AZURE_KEY")
WABA_ID = os.getenv("WABA_ID")
WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN")
