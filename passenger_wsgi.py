# -*- coding: utf-8 -*-
"""cPanel / Passenger entry point (MilesWeb, Hostinger, Namecheap …).

cPanel → Setup Python App → "Application startup file": passenger_wsgi.py
Environment variables (cPanel → Setup Python App → Environment variables):
    EXAM_DB=/home/<cpanel-user>/examportal/exam_portal.db
    EXAM_ADMIN_KEY=<mee secret key>

The same file also lets you run the portal behind gunicorn/uwsgi on a VPS:
    gunicorn --workers 2 --bind 0.0.0.0:8080 passenger_wsgi:application
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from exam_portal.wsgi import application  # noqa: E402,F401  (Passenger needs this name)
