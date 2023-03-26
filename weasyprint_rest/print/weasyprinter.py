import io
import os

from weasyprint import HTML

from weasyprint_rest.web.util import encrypt
from .template import Template


class WeasyPrinter:

    def __init__(self, html=None, url=None, template=None):
        self.html = html
        self.url = url
        self.template = template if template is not None else Template()

    def write(self, password=None, optimize_size=()):
        if self.url is not None:
            html = HTML(url=self.url, encoding="utf-8", url_fetcher=self.template.url_fetcher)
        else:
            html = HTML(file_obj=self.html, encoding="utf-8", url_fetcher=self.template.url_fetcher,
                        base_url=os.getcwd())
        font_config = self.template.get_font_config()
        styles = self.template.get_styles() if self.template is not None else []

        pdf_bytes = html.write_pdf(stylesheets=styles, image_cache=None, font_config=font_config,
                                   optimize_size=optimize_size)
        if password is None:
            return pdf_bytes

        out_file = io.BytesIO()
        encrypt(io.BytesIO(pdf_bytes), password, out_file)

        return out_file.getvalue()

    def close(self):
        pass
