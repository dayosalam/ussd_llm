from pathlib import Path
import os
from dotenv import load_dotenv

ENV_PATH: Path = Path(__file__).parents[2] / ".env.shared"
load_dotenv(ENV_PATH)
PORT_RUST = os.getenv("PORT_RUST")
PORT_LLM = os.getenv("PORT_LLM")
DOMAIN = os.getenv("DOMAIN")
PAY = os.getenv("PAY")
QR_PAY = os.getenv("QR_PAY")
DEV_PAY = os.getenv("DEV_PAY")
