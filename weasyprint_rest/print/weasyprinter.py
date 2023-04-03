import io
import logging
import os
import shutil
import uuid

import pdfkit
from weasyprint import HTML
from werkzeug.utils import secure_filename

from weasyprint_rest.env import is_debug_mode
from weasyprint_rest.web.util import encrypt
from .template import Template

TMP_TEMPLATE_BASE = "/tmp/template_"


def get_temp_dir(template, assets_count):
    if template is None or assets_count > 0:
        return "{0}{1}/".format(TMP_TEMPLATE_BASE, str(uuid.uuid1()))

    return "{0}{1}/".format(TMP_TEMPLATE_BASE, secure_filename(template.name))


class WeasyPrinter:

    def __init__(self, html=None, url=None, template=None):
        self.html = html
        self.url = url
        self.template = template if template is not None else Template()

    def write(self, optimize_size, password=None, driver=None, options=None):

        if driver == 'wk':
            pdf_bytes = self._write_with_pdfkit(options)
        else:
            pdf_bytes = self._write_with_weasyprint(optimize_size)

        if password is None:
            return pdf_bytes

        out_file = io.BytesIO()
        encrypt(io.BytesIO(pdf_bytes), password, out_file)

        return out_file.getvalue()

    def _write_with_pdfkit(self, options):
        verbose = None
        if is_debug_mode():
            verbose = True

        if self.url is not None:
            return pdfkit.from_url(self.url, options=options, verbose=verbose)

        base_dir = self._prepare_base_dir()
        if base_dir is None:
            pdf_bytes = pdfkit.from_string(self.html.read().decode(), options=options, verbose=verbose)
        else:
            html_file = base_dir + str(uuid.uuid1()) + ".html"
            self.html.save(html_file)
            options['enable-local-file-access'] = None
            pdf_bytes = pdfkit.from_file(html_file, options=options, verbose=verbose)
            self._cleanup_dir(base_dir, html_file)
        return pdf_bytes

    def _prepare_base_dir(self):
        assets_count = len(self.template.assets)
        if self.template.base_template is None and assets_count == 0:
            logging.debug("No need to prepare dir")
            return None

        base_dir = get_temp_dir(self.template.base_template, assets_count)

        if os.path.exists(base_dir):
            logging.warning("Directory already exists")
            return base_dir
        else:
            os.makedirs(base_dir)

        if self.template.base_template is not None:
            for asset in self.template.base_template.assets:
                self.template.get_asset(asset).save(base_dir + asset)

        for asset in self.template.assets:
            if not os.path.exists(base_dir + asset):
                self.template.get_asset(asset).save(base_dir + asset)

        return base_dir

    def _write_with_weasyprint(self, optimize_size):
        if self.url is not None:
            html = HTML(url=self.url, encoding="utf-8", url_fetcher=self.template.url_fetcher)
        else:
            html = HTML(file_obj=self.html, encoding="utf-8", url_fetcher=self.template.url_fetcher,
                        base_url=os.getcwd())
        font_config = self.template.get_font_config()
        styles = self.template.get_styles() if self.template is not None else []
        pdf_bytes = html.write_pdf(stylesheets=styles, image_cache=None, font_config=font_config,
                                   optimize_size=optimize_size)
        return pdf_bytes

    def _cleanup_dir(self, base_dir, html_file):
        if self.template.base_template is None:
            shutil.rmtree(base_dir)
            return

        if html_file.startswith(TMP_TEMPLATE_BASE + self.template.base_template.name + "/"):
            os.remove(html_file)
        else:
            shutil.rmtree(base_dir)

    def close(self):
        pass
