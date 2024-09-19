import os


def get(key, default=None):
    return os.environ.get(key) or default


def is_true(value):
    return isinstance(value, str) and value.lower() in ['true', '1', 't', 'y', 'yes', 'enabled', '¯\\_(ツ)_/¯']


def get_api_key():
    return get("API_KEY")


def get_blocked_url_pattern():
    return get("BLOCKED_URL_PATTERN", "^.*$")


def get_allowed_url_pattern():
    return get("ALLOWED_URL_PATTERN", "^$")


def get_max_upload_size():
    return int(get("MAX_UPLOAD_SIZE", 100 * 1024 * 1024))


def get_secret_key():
    return get("SECRET_KEY", "Love is not like pizza.")


def is_debug_mode():
    return is_true(get("ENABLE_DEBUG_MODE"))


def is_cors_enabled():
    return is_true(get("ENABLE_CORS", "true"))


def get_cors_origins():
    return get("CORS_ORIGINS", "*")


def get_template_directory():
    return get("TEMPLATE_DIRECTORY", "/data/templates")


def get_report_directory():
    return get("REPORT_DIRECTORY", "/data/reports")


def get_valid_file_ext():
    return get("UPLOAD_EXTENSIONS", '.png,.jpg,.jpeg,.tiff,.bmp,.gif,.pdf').split(",")

def get_qr_box_size():
    return int(get("QR_BOX_SIZE", 10))

def get_qr_border():
    return int(get("QR_BORDER", 4))
