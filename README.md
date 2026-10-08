# Photo Scan

Turn ordered photographs of paper documents into cleaned, perspective-corrected PDFs. Processing runs on your computer; no API key, paid scanning service, or processing server is required.

## Use online — no installation

Open **[Photo Scan](https://deepdive-ai.github.io/photo-scan/)** in your browser. Choose photos, review or adjust the crop corners, choose color/grayscale/black-and-white, and download your scanned PDF. Multiple photos become ordered PDF pages.

Photos are processed entirely on your device and are not uploaded to a server. No account, API key, or payment is needed. The website runs on GitHub Pages with no paid backend. Browser memory limits apply; use JPEG/PNG if your phone exports HEIC. The PDF contains scanned images, not searchable OCR text.

The static website lives in `docs/`. Preview it with `python3 -m http.server 8765 --directory docs`.

## Desktop app

Requires Python 3.10+ with Tkinter. Download/extract the release archive, open a terminal in the extracted folder, and run:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python scan_app.py
```

On Windows:

```powershell
py -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python scan_app.py
```

Add JPEG, PNG, WebP or TIFF document photos. Select one page to move it up or down. Choose color (default), grayscale, or black-and-white and an A4, Letter, or original-size page. Save with a new filename and open the PDF to review it. If a crop omits content, turn off Automatic crop and save again. Some Python distributions require installing Tkinter separately. This is a Python app, not a signed native executable.

## Command line

```sh
.venv/bin/python skills/scan-photos/scripts/scan.py page1.jpg page2.jpg --output scanned.pdf --mode color --preview-dir previews
```

For manual perspective correction, use `--corners corners.json`. The JSON contains one entry per page, with four normalized `[x,y]` coordinates in top-left, top-right, bottom-right, bottom-left order. Coordinates refer to the EXIF-corrected image after any explicit rotation. Use null for automatic detection on an individual page.

```json
[[[0.1,0.1],[0.9,0.1],[0.9,0.9],[0.1,0.9]]]
```

Other options: `--no-crop`, `--rotate 90|180|270`, `--page-size a4|letter|original`.

## Agent plugin

The root `plugin.json` and `skills/scan-photos/` implement a portable skills-based plugin. Use a supported custom-plugin import flow and ask: “Use Photo Scan to turn these photos into a clean color PDF.” The host must execute Python and expose uploaded files and packaged scripts. Account/workspace capabilities determine availability. Public ChatGPT installation and execution have not been verified. This is not an approved Plugin Directory listing.

## Quality and privacy

Automatic cropping works best with light paper on a contrasting background. It includes a fallback for portrait photos with visible top/bottom boundaries and clipped side edges. Crops still require visual review; a narrow outer margin may remain. Soft-shadow cleanup is available in grayscale/black-and-white; color uses contrast adjustment. Black-and-white can lose faint writing.

No OCR/searchable text, curved-page flattening, glare removal or blur recovery is provided. Missing photo content cannot be recovered. Maximum 50 photos; images are reduced to at most 3000 pixels along the longest edge. HEIC needs an additional decoder or conversion to JPEG.

The scanner and desktop launcher make no network requests. Dependency installation downloads Python packages. Photos, PDFs and previews stay in the selected local locations and are not automatically deleted. Agent-host uploads remain subject to that host's data policies.

## Tests

```sh
.venv/bin/python -m pip install -r requirements-dev.txt
.venv/bin/python -m unittest discover -s tests -v
```

Five tests cover multi-page count and ordering, all scan modes, manual/automatic crop, clipped-edge detection, fallback, original preservation, overwrite rejection and failed-input cleanup. One real document photo was checked locally by rendering its PDF. The desktop GUI has not received interactive testing on every supported operating system.

## Publishing and costs

This download runs on the user's computer, so its publisher does not host photo-processing infrastructure. Users supply their own Python runtime and device. Maintenance means fixing reported bugs and updating dependencies. No paid service has been configured. GitHub public downloads are the intended first distribution channel. Public ChatGPT submission remains a separate, unverified release path.

Only source code, instructions and synthetic tests belong in this release. Personal photographs, generated document PDFs, account details and credentials are excluded.
