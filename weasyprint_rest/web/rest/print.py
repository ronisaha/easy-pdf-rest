#!/usr/bin/python
# -*- coding: utf-8 -*-
import io
import json
import os

from flask import request, abort, make_response, render_template
from flask_restful import Resource
from werkzeug.datastructures import FileStorage

from ..util import authenticate
from ...print.template import Template
from ...print.template_loader import TemplateLoader
from ...print.weasyprinter import WeasyPrinter


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


class PrintAPI(Resource):
    decorators = [authenticate]

    def __init__(self):
        super(PrintAPI, self).__init__()

    def post(self):

        driver = _parse_request_argument("driver", 'weasy')
        url = _parse_request_argument("url", None)
        report = _parse_request_argument("report", None)
        optimize_images = _parse_request_argument("optimize_images", False)

        if driver not in['weasy', 'wk']:
            return abort(422, description="Invalid value for driver! only wk or weasy supported")

        html = None

        if report is not None:
            try:
                data = json.loads(_parse_request_argument("data", '{}'))
                content = render_template(report, **data)
                html = FileStorage(
                    stream=io.BytesIO(bytes(content, encoding='utf8')),
                    content_type="text/html"
                )
            except (ValueError, TypeError):
                return abort(400, description="Invalid data provided")
            except Exception as te:
                return abort(400, description=te)

        elif url is None:
            html = _parse_request_argument("html", None, "file", {
                "content_type": "text/html"
            })

        if html is None and url is None:
            return abort(422, description="Required argument 'html' or 'url' or report is missing.")

        template = _build_template()
        printer = WeasyPrinter(html=html, url=url, template=template)

        password = _parse_request_argument("password", None)

        options = None
        if driver == 'wk':
            options = json.loads(_parse_request_argument("options", '{}'))

        content = printer.write(optimize_images, password=password, driver=driver, options=options)

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
