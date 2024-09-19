import time
import os
import hashlib
import mimetypes
from werkzeug.datastructures import FileStorage
from weasyprint_rest.print.template_loader import TemplateLoader
from PIL import Image
import base64
from io import BytesIO


def test_app():
    pass


def test_may_update_result(client):
    if os.getenv('ENABLE_BUILD_IMAGE_UPDATE') == "true":
        res = client.post(
            "/api/v1.0/print",
            content_type='multipart/form-data',
            data=get_print_input(),
            headers=auth_header()
        )
        data = res.get_data()
        write_file(get_path("./resources/report"), "result.png", data)
    assert True


def test_get_health_status(client):
    res = client.get("/api/v1.0/health")
    assert "status" in res.json and res.json["status"] == "OK"


def test_get_health_timestamp(client):
    min_time = round(time.time() * 1000)
    max_time = min_time + 1000
    res = client.get("/api/v1.0/health")
    assert "timestamp" in res.json and min_time <= int(res.json["timestamp"]) <= max_time


def test_post_print_png(client):
    res = client.post(
        "/api/v1.0/print",
        content_type='multipart/form-data',
        data=get_print_input(),
        headers=auth_header()
    )
    assert res.status_code == 200

    data = res.get_data()
    assert verify_output(data)


def test_post_print_png_css_asset(client):
    req_data = get_print_input(False)
    req_data.get("asset[]").append(req_data["style"])
    del req_data["style"]

    res = client.post(
        "/api/v1.0/print",
        content_type='multipart/form-data',
        data=req_data,
        headers=auth_header()
    )
    assert res.status_code == 200

    data = res.get_data()
    assert verify_output(data)


def test_post_print_pdf(client):
    data = get_print_input()
    data["mode"] = "pdf"
    res = client.post(
        "/api/v1.0/print",
        content_type='multipart/form-data',
        data=data,
        headers=auth_header()
    )
    assert res.status_code == 200


def test_post_print_no_mode(client):
    data = get_print_input()
    del data["mode"]
    res = client.post(
        "/api/v1.0/print",
        content_type='multipart/form-data',
        data=data,
        headers=auth_header()
    )
    assert res.status_code == 200 and res.headers['Content-Type'] == "application/pdf"


def test_post_print_mode_as_argument(client):
    data = get_print_input()
    del data["mode"]
    res = client.post(
        "/api/v1.0/print?mode=png",
        content_type='multipart/form-data',
        data=data,
        headers=auth_header()
    )
    assert res.status_code == 200 and res.headers['Content-Type'] == "image/png"


def test_post_print_foreign(client):
    data = get_print_input()
    del data["mode"]
    res = client.post(
        "/api/v1.0/print?mode=png",
        content_type='multipart/form-data',
        data=data,
        headers=auth_header()
    )
    assert res.status_code == 200 and res.headers['Content-Type'] == "image/png"


def test_post_print_foreign_url_deny(client):
    res = client.post(
        "/api/v1.0/print",
        content_type='multipart/form-data',
        data=get_print_input(),
        headers=auth_header()
    )
    assert res.status_code == 200

    data = res.get_data()
    assert verify_output(data)


def test_post_print_foreign_url_allow(client, monkeypatch):
    monkeypatch.setenv("ALLOWED_URL_PATTERN", ".*", prepend=False)
    res = client.post(
        "/api/v1.0/print",
        content_type='multipart/form-data',
        data=get_print_input(),
        headers=auth_header()
    )

    assert res.status_code == 200
    data = res.get_data()
    assert not verify_output(data)


def test_post_print_access_deny(client):
    res = client.post(
        "/api/v1.0/print",
        content_type='multipart/form-data'
    )
    assert res.status_code == 401


def test_post_print_html_missing_params(client):
    res = client.post(
        "/api/v1.0/print",
        content_type='multipart/form-data',
        headers=auth_header()
    )
    assert res.status_code == 422


def test_post_print_html_without_css_assets(client):
    data = get_print_input(False)
    del data["style"]
    data["asset[]"] = []
    res = client.post(
        "/api/v1.0/print",
        content_type='multipart/form-data',
        data=data,
        headers=auth_header()
    )
    assert res.status_code == 200


def get_print_input(use_template=True):
    input_dir = get_path("./resources/report")
    template_dir = get_path("./resources/templates/report")

    data = {
        "mode": "png",
        "html": read_file(input_dir, "report.html"),
    }

    if use_template:
        data["template"] = "report"
    else:
        data.update({
            "style": read_file(template_dir, "report.css"),
            "asset[]": [
                # TODO: Fonts does currently not work
                read_file(template_dir, "FiraSans-Bold.otf"),
                read_file(template_dir, "FiraSans-Italic.otf"),
                read_file(template_dir, "FiraSans-LightItalic.otf"),
                read_file(template_dir, "FiraSans-Light.otf"),
                read_file(template_dir, "FiraSans-Regular.otf"),
                read_file(template_dir, "heading.svg"),
                read_file(template_dir, "internal-links.svg"),
                read_file(template_dir, "multi-columns.svg"),
                read_file(template_dir, "report-cover.jpg"),
                read_file(template_dir, "style.svg"),
                read_file(template_dir, "table-content.svg")
            ]
        })

    return data


def read_file(path, filename):
    abs_path = os.path.join(path, filename)
    return FileStorage(
        stream=open(abs_path, "rb"),
        filename=filename,
        content_type=mimetypes.guess_type(filename)[0],
    )


def write_file(path, filename, data):
    abs_path = os.path.join(path, filename)
    with open(abs_path, "wb") as file:
        file.write(data)


def verify_output(data):
    input_file = get_path("./resources/report/result.png")
    data_hash = hashlib.sha1(data).hexdigest()
    with open(input_file, "rb") as file:
        input_data = file.read()
        input_hash = hashlib.sha1(input_data).hexdigest()
        return data_hash == input_hash
    return False


def get_path(relative_path):
    dir_path = os.path.dirname(os.path.realpath(__file__))
    return os.path.join(dir_path, relative_path)


def auth_header():
    return {"X_API_KEY": "SECRET_API_KEY"}


def test_generate_qrcode():
    data = "This is a example Data"
    logo_path = get_path("./resources/templates/logo.png")

    # Generate QR code
    qr_code_data = TemplateLoader.generate_qrcode(data, logo_path)

    # Check if QR code data is generated
    assert qr_code_data is not None

    # Decode the base64 string to verify the image
    qr_code_bytes = base64.b64decode(qr_code_data.split(",")[1])
    qr_code_image = Image.open(BytesIO(qr_code_bytes))

    # Check if the image is a valid QR code
    assert qr_code_image.format == "PNG"
    assert qr_code_image.size[0] > 0 and qr_code_image.size[1] > 0


def get_path(relative_path):
    dir_path = os.path.dirname(os.path.realpath(__file__))
    return os.path.join(dir_path, relative_path)


def test_html_template():
    data = "This is a example Data"
    logo_path = get_path("./resources/templates/logo.png")

    # Generate QR code
    qr_code_data = TemplateLoader.generate_qrcode(data, logo_path)

    # Create HTML template with QR code
    html_template = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>QR Code Example</title>
    </head>
    <body>
        <h1>QR Code Example</h1>
        <img src="{qr_code_data}" alt="QR Code">
    </body>
    </html>
    """

    # Check if the HTML template contains the QR code data
    assert qr_code_data in html_template
