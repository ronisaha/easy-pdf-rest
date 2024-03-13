#!/usr/bin/python
# -*- coding: utf-8 -*-
import io
import json
import logging
import os

from flask import request, abort, make_response, render_template
from flask_restful import Resource
from pypdf import PdfMerger
from werkzeug.datastructures import FileStorage

from ..util import authenticate
from ...print.template import Template
from ...print.template_loader import TemplateLoader
from ...print.weasyprinter import WeasyPrinter, encrypt_pdf


def _get_request_list_or_value(request_dict, name):
    return request_dict.getlist(name) if name.endswith("[]") else request_dict[name]

def _get_request_argument(name, default=None):
    form = request.form
    args = request.args
    files = request.files

    if name in form:
        return _get_request_list_or_value(form, name)
    elif name in args:
        return _get_request_list_or_value(args, name)
    elif name in files:
        return _get_request_list_or_value(files, name)
    return default


def _parse_request_argument(name, default=None, parse_type=None, parse_args=None):
    content = _get_request_argument(name, default)

    if parse_type == "file" and isinstance(content, str):
        content_type = _may_get_dict_value(parse_args, "content_type")
        return FileStorage(
            stream=io.BytesIO(bytes(content, encoding='utf8')),
            content_type=content_type
        )

    if content == default and name.endswith("[]"):
        content = _parse_request_argument(name[:-2], default, parse_type, parse_args)
        if not isinstance(content, list):
            return [content]

    return content


def _may_get_dict_value(dict_values, key, default=None):
    if dict_values is None:
        return default
    if key not in dict_values:
        return default
    return dict_values[key]


def _build_template():
    styles = _parse_request_argument("style[]", [], "file", {
        "content_type": "text/css",
        "file_name": "style.css"
    })
    assets = _parse_request_argument("asset[]", [])
    template_name = _parse_request_argument("template", None)
    base_template = TemplateLoader().get(template_name)

    return Template(styles=styles, assets=assets, base_template=base_template)


def convert_html2pdf(driver, html, template, url):
    printer = WeasyPrinter(html=html, url=url, template=template)
    options = None
    if driver == 'wk':
        options = json.loads(_parse_request_argument("options", '{}'))
    pdf_bytes = printer.write(driver=driver, options=options)
    return pdf_bytes


def render_report_template(report, **data):
    content = render_template(report, **data)
    return FileStorage(
        stream=io.BytesIO(bytes(content, encoding='utf8')),
        content_type="text/html"
    )


def get_multi_report_pdf(driver, report, template, data_arr):
    merger = PdfMerger()
    for data in data_arr:
        html = render_report_template(report, **data)
        pdf_bytes = convert_html2pdf(driver, html, template, None)
        merger.append(io.BytesIO(pdf_bytes))
    bytes_stream = io.BytesIO()
    merger.write(bytes_stream)

    return bytes_stream.getvalue()


class PrintAPI(Resource):
    decorators = [authenticate]

    def __init__(self):
        super(PrintAPI, self).__init__()

    def post(self):

        driver = _parse_request_argument("driver", 'weasy')
        url = _parse_request_argument("url", None)
        report = _parse_request_argument("report", None)
        data_set = _parse_request_argument("data_set", None)

        if driver not in ['weasy', 'wk']:
            return abort(422, description="Invalid value for driver! only wk or weasy supported")

        html = None
        pdf_bytes = None
        template = _build_template()

        if report is not None and data_set is not None:

            try:
                data_arr = json.loads(_parse_request_argument("data_set", '[]'))
            except (ValueError, TypeError) as te:
                logging.error(te)
                return abort(400, description="Invalid data provided")
            except Exception as te:
                logging.error(te)
                return abort(400, description="Unknown error occurred")

            if not isinstance(data_arr, list) or len(data_arr) == 0:
                return abort(400, description="Unknown error occurred")

            pdf_bytes = get_multi_report_pdf(driver, report, template, data_arr)
        elif report is not None:
            try:
                html = render_report_template(report, **(json.loads(_parse_request_argument("data", '{}'))))
            except (ValueError, TypeError) as te:
                logging.error(te)
                return abort(400, description="Invalid data provided")
            except Exception as te:
                logging.error(te)
                return abort(400, description="Unknown error occurred")

        elif url is None:
            html = _parse_request_argument("html", None, "file", {
                "content_type": "text/html"
            })

        if html is None and url is None and pdf_bytes is None:
            return abort(422, description="Required argument 'html' or 'url' or report is missing.")

        if pdf_bytes is None:
            pdf_bytes = convert_html2pdf(driver, html, template, url)

        password = _parse_request_argument("password", None)

        content = encrypt_pdf(pdf_bytes, password=password)

        # build response
        response = make_response(content)
        basename, _ = os.path.splitext(_parse_request_argument("file_name", 'document.pdf'))
        response.headers['Content-Type'] = 'application/pdf'
        disposition = _parse_request_argument("disposition", "inline")

        response.headers['Content-Disposition'] = '%s; name="%s"; filename="%s.%s"' % (
            disposition,
            basename,
            basename,
            "pdf"
        )

        if hasattr(html, 'close'):
            html.close()

        return response
