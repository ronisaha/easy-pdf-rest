#!/usr/bin/python
# -*- coding: utf-8 -*-

"""Alternative version of the ToDo RESTful server implemented using the
Flask-RESTful extension."""

import re
import logging

from flask import abort, request
from functools import wraps
from pypdf import PdfWriter, PdfReader

from ..env import (
    get_api_key, get_allowed_url_pattern, get_blocked_url_pattern
)


def encrypt(in_file, password, out_stream):
    pdf_reader = PdfReader(in_file)
    pdf_writer = PdfWriter()
    pdf_writer.append_pages_from_reader(pdf_reader)
    pdf_writer.encrypt(password, password + "owner")
    pdf_writer.write(out_stream)


def authenticate(func):
    @wraps(func)
    def verify_token(*args, **kwargs):
        try:
            authenticated = is_authenticated(request)
        except Exception:  # pragma: no cover
            return abort(401)

        if authenticated is True:
            return func(*args, **kwargs)
        else:
            abort(401)

    return verify_token


def is_authenticated(req):
    return (
        get_api_key() is None
        or ('X_API_KEY' in req.headers and get_api_key() == req.headers['X_API_KEY'])
    )


def check_url_access(url):
    allowed_url_pattern = get_allowed_url_pattern()
    blocked_url_pattern = get_blocked_url_pattern()

    try:
        if re.match(allowed_url_pattern, url):
            return True
        if re.match(blocked_url_pattern, url):
            return False
        return True  # pragma: no cover
    except Exception:  # pragma: no cover
        logging.error(
            "Could not parse one of the URL Patterns correctly. Therefor the URL %r was " +
            "blocked. Please check your configuration." % url
        )
        return False
