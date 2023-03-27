#!/usr/bin/python
# -*- coding: utf-8 -*-

import io
import json
import os
import uuid

from PIL import Image
from flask import current_app, request, abort, jsonify, make_response
from flask_restful import Resource
from pypdf import PdfMerger, PageRange
from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename

from ..util import authenticate, encrypt


def _get_request_list_or_value(request_dict, name):
    return request_dict.getlist(name) if name.endswith("[]") else request_dict[name]


def _parse_pages_input_string(input_string):
    output_list = []
    files = input_string.split()
    for file in files:
        if '~' in file:
            file_name, ranges = file.split('~')
            ranges = ranges.split(',')
            for r in ranges:
                output_list.append({
                    "file": file_name,
                    "range": r
                })
        else:
            output_list.append({
                "file": file
            })
    return output_list


def _read_page_definition(pages):
    try:
        return json.loads(pages)
    except ValueError:
        return _parse_pages_input_string(pages)


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
        file_name = _may_get_dict_value(parse_args, "file_name")
        return FileStorage(
            stream=io.BytesIO(bytes(content, encoding='utf8')),
            filename=file_name,
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


def image_to_pdf(uploaded_file):
    file_name, file_extension = os.path.splitext(uploaded_file.filename)
    converted_file_name = "{0}-{1}.pdf".format(str(uuid.uuid1()), secure_filename(file_name))
    image_1 = Image.open(uploaded_file)
    im_1 = image_1.convert('RGB')
    im_1.save(converted_file_name)
    return converted_file_name


class MergeAPI(Resource):
    decorators = [authenticate]

    def __init__(self):
        super(MergeAPI, self).__init__()
        self.uploaded_file_names = []

    def validate_uploaded_file_ext(self, file_extension):
        if file_extension not in current_app.config['UPLOAD_EXTENSIONS']:
            abort(400, description="Invalid file format {0}".format(file_extension))

    def validate_duplicate_uploaded_file_name(self, uploaded_file_name):
        if uploaded_file_name in self.uploaded_file_names:
            abort(400, description="Duplicate file name found {0}".format(uploaded_file_name))

    def post(self):
        if 'files[]' not in request.files:
            resp = jsonify({'message': 'No file part in the request'})
            resp.status_code = 400
            return resp

        password = _get_request_argument("password", None)
        pages = _parse_request_argument("pages", [])

        merger = PdfMerger()
        file_map = {}
        for uploaded_file in request.files.getlist('files[]'):
            file_name, file_extension = os.path.splitext(uploaded_file.filename)
            self.validate_uploaded_file_ext(file_extension)
            self.validate_duplicate_uploaded_file_name(file_name)

            file_map[uploaded_file.filename] = uploaded_file
            if file_extension != '.pdf':
                converted_file_name = image_to_pdf(uploaded_file)
                with open(converted_file_name, 'rb') as bites:
                    file_map[uploaded_file.filename] = bites

        for page_map in _read_page_definition(pages):
            if file_map.get(page_map['file']) is not None:
                if "range" in page_map and page_map['range'] != ':' and page_map['range'] != '':
                    merger.append(file_map[page_map['file']], pages=PageRange(page_map['range']))
                else:
                    merger.append(file_map[page_map['file']])

        bytes_stream = io.BytesIO()

        if password is None:
            merger.write(bytes_stream)
        else:
            in_file = io.BytesIO()
            merger.write(in_file)
            encrypt(in_file, password, bytes_stream)

        response = make_response(bytes_stream.getvalue())
        response.headers['Content-Disposition'] = 'attachment; filename=merged.pdf'
        response.mimetype = 'application/pdf'
        merger.close()
        bytes_stream.close()

        return response
