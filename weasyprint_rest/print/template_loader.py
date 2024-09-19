import base64
import glob
import json
import logging
import mimetypes
import os
from io import BytesIO

import qrcode
from PIL import Image
from werkzeug.datastructures import FileStorage

from .template import Template
from ..env import is_debug_mode


class TemplateLoader:
    instance = None

    def __init__(self):
        if not TemplateLoader.instance:
            TemplateLoader.instance = TemplateLoader.__TemplateLoader()

    def __getattr__(self, name):
        return getattr(self.instance, name)

    class __TemplateLoader:
        def __init__(self):
            self.template_definitions = {}

        def load(self, base_dir):
            for template_dir in os.listdir(base_dir):
                abs_template_dir = os.path.join(base_dir, template_dir)
                template_file = os.path.join(abs_template_dir, "template.json")
                if not os.path.isfile(template_file):
                    self.add_definition(abs_template_dir, {})
                    continue
                with open(template_file) as json_file:
                    self.add_definition(abs_template_dir, json.load(json_file))

        def add_definition(self, base_dir, definition):
            name = definition["name"] if "name" in definition else os.path.basename(base_dir)
            if name in self.template_definitions:
                logging.warn(
                    "Template %r found in %r was already defined. This template will be ignored" % (name, base_dir))
                return

            definition["name"] = name
            definition["base_dir"] = base_dir
            definition["prepared"] = False
            definition["template"] = None
            self.template_definitions[name] = definition

        def get(self, name):
            if name not in self.template_definitions:
                return None

            definition = self.template_definitions[name]

            if not definition["prepared"] or is_debug_mode():
                self._prepare_definition(definition)

            if not definition["template"] or is_debug_mode():
                self._build_template(definition)

            return definition["template"]

        def _prepare_definition(self, definition):
            base_dir = definition["base_dir"]

            if "styles" not in definition:
                definition["styles"] = self._detect_file_locations(base_dir, "**/*.css")

            if "assets" not in definition:
                definition["assets"] = self._detect_file_locations(base_dir, "**/*")

            definition["prepared"] = True

        def _detect_file_locations(self, base_dir, search_pattern):
            return [
                name for name in glob.glob(os.path.join(base_dir, search_pattern), recursive=True)
            ]

        def _build_template(self, definition):
            base_dir = definition["base_dir"]

            styles = self._read_files(base_dir, definition["styles"])
            assets = self._read_files(base_dir, definition["assets"])

            template = Template(styles=styles, assets=assets, name=definition['name'])
            definition["template"] = template

        def _read_files(self, base_dir, file_locations):
            files = []
            for file in file_locations:
                if not os.path.isfile(file):
                    continue

                files.append(FileStorage(
                    stream=open(file, "rb"),
                    filename=os.path.relpath(file, base_dir),
                    content_type=mimetypes.guess_type(file)[0]
                ))
            return files

    def generate_qrcode(data, logo_path=None):
        try:
            template_directory = os.getenv('TEMPLATE_DIRECTORY', '/data/templates')
            box_size = int(os.getenv('QR_BOX_SIZE', 10))
            border = int(os.getenv('QR_BORDER', 4))

            if logo_path:
                logo_path = os.path.join(template_directory, logo_path)
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_H,
                box_size=box_size,
                border=border,
            )
            qr.add_data(data)
            qr.make(fit=True)

            img = qr.make_image(fill_color='black', back_color='white').convert('RGB')
            if logo_path and os.path.exists(logo_path):
                logo = Image.open(logo_path)
                if logo.mode in ('P', 'LA') or (logo.mode == 'RGBA' and 'transparency' in logo.info):
                    logo = logo.convert('RGBA')
                logo_size = min(img.size[0] // 5, img.size[1] // 5)
                logo = logo.resize((logo_size, logo_size), Image.LANCZOS)
                mask = logo.split()[3] if logo.mode == 'RGBA' else None
                pos = ((img.size[0] - logo_size) // 2, (img.size[1] - logo_size) // 2)
                img.paste(logo, pos, mask=mask)

            buffer = BytesIO()
            img.save(buffer, format="PNG")
            img_str = base64.b64encode(buffer.getvalue()).decode("utf-8")
            return f"data:image/png;base64,{img_str}"

        except Exception as e:
            print(f"Error generating QR code: {e}")
            return None
