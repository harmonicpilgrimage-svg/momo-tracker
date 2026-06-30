# ============================================
# MoMo Tracker - Configuration
# ============================================
import os
from dotenv import load_dotenv

load_dotenv()

# MTN MoMo API Keys
COLLECTION_PRIMARY_KEY = os.getenv("COLLECTION_PRIMARY_KEY", "")
COLLECTION_SECONDARY_KEY = os.getenv("COLLECTION_SECONDARY_KEY", "")
COLLECTION_REF_ID = os.getenv("COLLECTION_REF_ID", "")
COLLECTION_API_KEY = os.getenv("COLLECTION_API_KEY", "")

DISBURSEMENT_PRIMARY_KEY = os.getenv("DISBURSEMENT_PRIMARY_KEY", "")
DISBURSEMENT_SECONDARY_KEY = os.getenv("DISBURSEMENT_SECONDARY_KEY", "")
DISBURSEMENT_REF_ID = os.getenv("DISBURSEMENT_REF_ID", "")
DISBURSEMENT_API_KEY = os.getenv("DISBURSEMENT_API_KEY", "")

# Your MoMo phone number (format: 250XXXXXXXXX)
MOMO_PHONE_NUMBER = os.getenv("MOMO_PHONE_NUMBER", "250780000000")

# API URLs
MOMO_SANDBOX_HOST = "sandbox.momodeveloper.mtn.com"
MOMO_BASE_URL = f"https://{MOMO_SANDBOX_HOST}"

# Currency: EUR for sandbox, RWF for production Rwanda
CURRENCY = os.getenv("CURRENCY", "EUR")

# App settings
SECRET_KEY = os.getenv("SECRET_KEY", "change-me-to-something-random")
DEBUG = os.getenv("DEBUG", "true").lower() == "true"
