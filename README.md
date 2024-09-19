<div align="center">
	<p>
		<a href="https://github.com/ronisaha/easy-pdf-rest#is=awesome">
			<img width="90%" src="https://raw.githubusercontent.com/ronisaha/easy-pdf-rest/develop/resources/logo.svg?sanitize=true"/>
		</a>
	</p>
	<hr>
	<p>
		Rest Service and docker image for pdf processing.
	</p>
</div>

## Usage

First, you can start the container using the following command:

```bash
docker run -p 5000:5000 -v /path/to/local/dir:/data -d ronisaha/easy-pdf-rest:latest
```

Then you can use the following command to generate the report.pdf from the official WeasyPrint sample. You can find the files in `tests/resources/report`.

```bash
curl  \
-F 'html=@report.html' \
-H X-API-KEY:key \
-F 'style=@report.css' \
-F "asset[]=@FiraSans-Bold.otf" \
-F "asset[]=@FiraSans-Italic.otf" \
-F "asset[]=@FiraSans-LightItalic.otf" \
-F "asset[]=@FiraSans-Light.otf" \
-F "asset[]=@FiraSans-Regular.otf" \
-F "asset[]=@heading.svg" \
-F "asset[]=@internal-links.svg" \
-F "asset[]=@multi-columns.svg" \
-F "asset[]=@report-cover.jpg" \
-F "asset[]=@style.svg" \
-F "asset[]=@table-content.svg" \
-F "asset[]=@thumbnail.png" \
http://localhost:5000/api/v1.0/print --output report.pdf
```

## Configuration



All configurations are set via environment variables.

| Name                  | Default                                | Description                                                                                                                                                                                           |
|-----------------------|----------------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `API_KEY`             | `""`                                   | Sets an API key that protects the `/api/v1.0/print` service from unauthorized access. The key is later compared with the header `X_API_KEY`. If no API_KEY is set, anyone can access the application. |
| `BLOCKED_URL_PATTERN` | `"^.*$"`                               | Pattern to block certain URLs. These URLs are later not allowed within resources of the print service. These resources will be ignored.                                                               |
| `ALLOWED_URL_PATTERN` | `"^$"`                                 | Pattern to allow certain URLs. These URLs are later allowed within resources of the print service.                                                                                                    |
| `MAX_UPLOAD_SIZE`     | `104857600`                            | Maximum size of the upload. Default is `100MB`                                                                                                                                                        |
| `UPLOAD_EXTENSIONS`   | `.png,.jpg,.jpeg,.tiff,.bmp,.gif,.pdf` | Allowed extensions while using merge endpoint                                                                                                                                                         |
| `TEMPLATE_DIRECTORY`  | `/data/templates`                      | Base path for templates                                                                                                                                                                               |
| `REPORT_DIRECTORY`    | `/data/reports`                        | Base path for Jinja template                                                                                                                                                                          |

## Services

### Health

Service to check if the service is still working properly.

```http
GET /api/v1.0/health
```

#### Parameters

| Parameter | Type     | Description                                          |
|:----------|:---------|:-----------------------------------------------------|
| `ping`    | `string` | __Optional__. Returns the `ping` in the field `pong` |

#### Response

```json
{
  "status": "OK",
  "weasyprint": "string",
  "wkhtmltopdf": "string",
  "pypdf": "string",
  "Pillow": "string",
  "pdfkit": "string",
  "timestamp": "number",
  "pong": "string?"
}
```

The `status` does always contain "OK".

The `weasyprint` does contain the current weasyprint version.

The `timestamp` does contain the current timestamp of the server in milliseconds.

The `pong` is optional and will only be sent if the `ping` parameter was passed. It contains the same value that `ping` had.

### Print

Service to print a pdf or png

```http
POST /api/v1.0/print
```

#### Parameters

| Parameter         | Type             | Required          | Description                                                                                                                                                                                                               |
|:------------------|:-----------------|:------------------|:--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `html`            | `file or string` | __Semi-Required__ | HTML file to convert. html or url or report one is required. Only either url or html, report should be used.                                                                                                              |
| `url`             | `file or string` | __Semi-Required__ | URL to convert. html or url or report one is required. Only either url or html, report should be used.                                                                                                                    |
| `report`          | `string`         | __Semi-Required__ | Report template name to render the html. html or url or report one is required. Only either url or html, report should be used.                                                                                           |
| `data`            | `dict`           | __Semi-Required__ | Variables as dictionary for rendering report template. Used along with `report` parameter. Only either `data` or `data_set` should be used.                                                                               |
| `data_set`        | `dict[]`         | __Semi-Required__ | List of "Variables as dictionary" for rendering multiple report. Used along with `report` parameter. Only either `data` or `data_set` should be used.                                                                     |
| `optimize_images` | `boolean`        | __Optional__      | Whether size of embedded images should be optimized, with no quality loss.                                                                                                                                                |
| `disposition`     | `string`         | __Optional__      | Set response `disposition` type(attachment or inline). default is inline.                                                                                                                                                 |
| `file_name`       | `string`         | __Optional__      | Set response `disposition file_name`. default is `document.pdf`.                                                                                                                                                          |
| `password`        | `string`         | __Optional__      | Password protected PDF                                                                                                                                                                                                    |
| `template`        | `string`         | __Optional__      | Template name for the use of predefined templates.                                                                                                                                                                        |
| `driver`          | `string`         | __Optional__      | `wk\|weasy(default)` wk=`wkhtnltopdf` weasy=`Weasyprint`                                                                                                                                                                  |
| `options`         | `json`           | __Optional__      | Only with driver=`wk` all supported `wkhtmltopdf` options are supported                                                                                                                                                   |
| `style`           | `file or string` | __Optional__      | Style to apply to the `html`. This should only be used if the CSS is not referenced in the html. If it is included via HTML link, it should be passed as `asset`. Only either `style` or `style[]` can be used.           |
| `style[]`         | `file or file[]` | __Optional__      | Multiple styles to apply to the `html`. This should only be used if the CSS is not referenced in the html. If it is included via HTML link, it should be passed as `asset`. Only either `style` or `style[]` can be used. |
| `asset[]`         | `file or file[]` | __Optional__      | Assets which are referenced in the html. This can be images, CSS or fonts. The name must be 1:1 the same as used in the files.                                                                                            |


#### Response

Raw output stream of with `Content-Type` of `application/pdf` also the header `Content-Disposition = 'inline;filename={HTML_FILE_NAME}.pdf` will be set.


### Merge

Service to merge pdf and/or images

```http
POST /api/v1.0/merge
```

#### Parameters

| Parameter     | Type            | Required     | Description                                                               |
|:--------------|:----------------|:-------------|:--------------------------------------------------------------------------|
| `files[]`     | `file or files` | __Required__ | PDF or Image file                                                         |
| `pages`       | `string`        | __Required__ | Pages definition as string or `JSON`                                      |
| `disposition` | `string`        | __Optional__ | Set response `disposition` type(attachment or inline). default is inline. |
| `file_name`   | `string`        | __Optional__ | Set response `disposition file_name`. default is `merged.pdf`.            |
| `password`    | `string`        | __Optional__ | Password protected PDF                                                    |

##### pages can be passed as JSON

```json
[
  {
    "file": "file1.pdf",
    "range": "0:2"
  },
  {
    "file": "a.jpeg"
  },
  {
    "file": "file1.pdf",
    "range": "2:3"
  },
  {
    "file": "file2.pdf"
  }
]
```
**or string like:**
```code
file1.pdf~0:2 a.jpeg file1.pdf~2:3 file2.pdf
```

#### Range Syntext

| Range | Description                 |     | Range | Description             |
|-------|-----------------------------|-----|-------|-------------------------|
| :     | all pages.                  |     | -1    | last page.              |
| 22    | just the 23rd page.         |     | :-1   | all but the last page.  |
| 0:3   | the first three pages.      |     | -2    | second-to-last page.    |
| :3    | the first three pages.      |     | -2:   | last two pages.         |
| 5:    | from the sixth page onward. |     | -3:-1 | third & second to last. |

##### The third, "stride" or "step" number is also recognized.

| Range  | Description                 |     | Range  | Description      |
|--------|-----------------------------|-----|--------|------------------|
| ::2    | 0 2 4 ... to the end.       |     | 3:0:-1 | 3 2 1 but not 0. |
| 1:10:2 | 1 3 5 7 9                   |     | 2::-1  | 2 1 0.           |
| ::-1   | all pages in reverse order. |     |        |                  |

#### Response

Raw output stream of with `Content-Type` of `application/pdf` also the header `Content-Disposition = 'inline;filename=merged.pdf` will be set.

Attribution
-----------
This library was a forked from [weasyprint-rest](https://github.com/xpublisher/weasyprint-rest).

## Library and tools insides

It usages following tools and libraries

1. [WeasyPrint - the awesome document factory](https://weasyprint.org/)
2. [WK&lt;html&gt;toPDF - command line tools to render HTML into PDF](https://wkhtmltopdf.org/)
3. [pypdf - pure-python PDF library](https://pypi.org/project/pypdf/) capable of splitting, [merging](https://pypdf.readthedocs.io/en/stable/user/merging-pdfs.html), [cropping, and transforming](https://pypdf.readthedocs.io/en/stable/user/cropping-and-transforming.html)
4. [Pillow - the Python Imaging Library](https://pypi.org/project/Pillow/)
5. [pdfkit - wrapper for wkhtmltopdf](https://pypi.org/project/pdfkit/)


## QR Code Functionality

To use the QR code generation functionality in your templates, follow these steps:

1. **Add the QR Code Filter**: Ensure that the `generate_qrcode` function is registered as a Jinja2 filter named `QRCODE` in your Flask application.

2. **Use the Filter in Templates**: You can use the `QRCODE` filter in your HTML templates to generate QR codes. For example:

    ```html
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>QR Code Example</title>
    </head>
    <body>
        <h1>QR Code Example</h1>
        <img src="{{ data|QRCODE('logo.png') }}" alt="QR Code">
    </body>
    </html>
    ```

3. **Parameters**: The `QRCODE` filter takes two parameters:
    - `data`: The data to encode in the QR code.
    - `logo_path` (optional): The path to a logo image to embed in the center of the QR code. The path should be relative to the template directory.

4. **Template Directory**: Ensure that the `TEMPLATE_DIRECTORY` environment variable is set to the path of your template directory. The default is `/data/templates`.

    ```bash
    export TEMPLATE_DIRECTORY=/path/to/your/templates
    ```

5. **QR Code Size and Border**: You can set the size and border of the QR code using the following environment variables:

    ```bash
    export QR_BOX_SIZE=10  # Default is 10
    export QR_BORDER=4     # Default is 4
    ```
