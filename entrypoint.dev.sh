#!/bin/sh
python manage.py collectstatic --noinput
python manage.py migrate
gunicorn -c MenuBot/gunicorn.conf.py --reload