<div align="center">
	<p>
		<a href="https://github.com/ronisaha/easy-pdf-rest#is=awesome">
			<img width="90%" src="https://raw.githubusercontent.com/ronisaha/easy-pdf-rest/develop/resources/logo.svg?sanitize=true"/>
		</a>
	</p>
	<hr>
	<p>
		Service and docker image for <a href="https://weasyprint.org/">WeasyPrint - the awesome document factory</a>
	</p>
</div>

## Usage

First, you can start the container using the following command:

```bash
docker run -p 5000:5000 -v /path/to/local/templates:/data/templates -d ronisaha/easy-pdf-rest:latest
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
  "status"    : "OK",
  "timestamp" : number,
  "pong"      : string?
}
```

The `status` does always contain "OK".

The `timestamp` does contain the current timestamp of the server in milliseconds.

The `pong` is optional and will only be sent if the `ping` parameter was passed. It contains the same value that `ping` had.

### Print

Service to print a pdf or png

```http
POST /api/v1.0/print
```

#### Parameters

| Parameter  | Type             | Required          | Description                                                                                                                                                                                                               |
|:-----------|:-----------------|:------------------|:--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `html`     | `file or string` | __Semi-Required__ | HTML file to convert. html or url one is required. Only either url or html should be used.                                                                                                                                |
| `url`      | `file or string` | __Semi-Required__ | URL to convert. html or url one is required. Only either url or html should be used.                                                                                                                                      |
| `optimize` | `string`         | __Optional__      | Optimize size of generated PDF. Can contain Coma seperated "images" and "fonts".                                                                                                                                          |
| `password` | `string`         | __Optional__      | Password protected PDF                                                                                                                                                                                                    |
| `template` | `string`         | __Optional__      | Template name for the use of predefined templates.                                                                                                                                                                        |
| `style`    | `file or string` | __Optional__      | Style to apply to the `html`. This should only be used if the CSS is not referenced in the html. If it is included via HTML link, it should be passed as `asset`. Only either `style` or `style[]` can be used.           |
| `style[]`  | `file or file[]` | __Optional__      | Multiple styles to apply to the `html`. This should only be used if the CSS is not referenced in the html. If it is included via HTML link, it should be passed as `asset`. Only either `style` or `style[]` can be used. |
| `asset[]`  | `file or file[]` | __Optional__      | Assets which are referenced in the html. This can be images, CSS or fonts. The name must be 1:1 the same as used in the files.                                                                                            |


#### Response

Raw output stream of with `Content-Type` of `application/pdf` also the header `Content-Disposition = 'inline;filename={HTML_FILE_NAME}.pdf` will be set.


### Merge

Service to merge pdf and/or images

```http
POST /api/v1.0/merge
```

#### Parameters

| Parameter  | Type            | Required     | Description                          |
|:-----------|:----------------|:-------------|:-------------------------------------|
| `files[]`  | `file or files` | __Required__ | PDF or Image file                    |
| `pages`    | `string`        | __Required__ | Pages definition as string or `JSON` |
| `password` | `string`        | __Optional__ | Password protected PDF               |

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

