import os

SERVER_HOST = os.getenv('SERVER_HOST', "0.0.0.0")
SERVER_PORT = int(os.getenv('SERVER_PORT', "8501"))
SERVER_TIMEOUT = int(os.getenv('SERVER_TIMEOUT', "60"))

bind = f"{SERVER_HOST}:{SERVER_PORT}"
timeout = SERVER_TIMEOUT
workers = 4
worker_timeout = SERVER_TIMEOUT
