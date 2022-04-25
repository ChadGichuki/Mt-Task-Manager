from functools import wraps
from tkinter import N
from flask import redirect, session
import requests


def login_required(f):
    """Restricts access if a user is not logged in"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function


def get_quote():
    # Contact the API
    try:
        url = f"https://www.quotepub.com/api/widget/?type=qotd_t"
        response = requests.get(url)
        response.raise_for_status()
    except requests.RequestException:
        return None

    # Parse the response
    try:
        quote = response.json()
        return {
            "body": quote["quote_body"],
            "author": quote["quote_author"],
            "vendor": quote["quote_vendor"]
        }
    except (KeyError, TypeError, ValueError):
        return None
