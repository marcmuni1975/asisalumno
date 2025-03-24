#!/bin/bash
export FLASK_APP=app.py
export FLASK_ENV=production
export PORT=${PORT:-8080}
pip install -r requirements.txt
gunicorn --bind 0.0.0.0:$PORT wsgi:app
