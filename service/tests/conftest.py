import os


# Keep test collection independent from local MySQL configuration.
os.environ["DB_TYPE"] = "memory"
