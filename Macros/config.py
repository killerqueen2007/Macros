"""Shared paths and config loading."""
import json
import os
import time

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(BASE_DIR, "config.json")
USER_FUNCTIONS_DIR = os.path.join(BASE_DIR, "user_functions")

os.makedirs(USER_FUNCTIONS_DIR, exist_ok=True)


def load_config(path=CONFIG_PATH):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

