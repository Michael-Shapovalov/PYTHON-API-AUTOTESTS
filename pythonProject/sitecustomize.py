import os

from dotenv import load_dotenv


# TestIT adapter reads env vars during pytest plugin initialization,
# which happens before tests/conftest.py is imported.
# Loading .env here makes TMS_* available early.
_HERE = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(_HERE, ".env"))

