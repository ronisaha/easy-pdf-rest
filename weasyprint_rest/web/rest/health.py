#!/usr/bin/python
# -*- coding: utf-8 -*-

import time
from flask import request
from flask_restful import Resource
from weasyprint import __version__ as version
from pypdf import __version__ as version_pypdf
from PIL import __version__ as version_pil
from pdfkit import __version__ as version_pdfkit

from weasyprint_rest.web.util import is_authenticated


class HealthAPI(Resource):

    def __init__(self):
        super(HealthAPI, self).__init__()

    def get(self):
        pong = request.args.get('ping', '')

        return {
            "status": "OK",
            **({
                   "weasyprint": version,
                   "wkhtmltopdf": "0.12.6 (with patched qt)",
                   "pypdf": version_pypdf,
                   "Pillow": version_pil,
                   "pdfkit": version_pdfkit,
                   "timestamp": round(time.time() * 1000)
               } if is_authenticated(request) else {}),
            **({"pong": pong} if pong else {})
        }, 200
