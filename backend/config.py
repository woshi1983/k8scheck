import os
from dotenv import load_dotenv

load_dotenv()

K8S_ENV = os.getenv("K8S_ENV", "mock")
