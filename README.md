# Free Photo to Scanned PDF (color/grayscale)

**[Open the free online tool](https://deepdive-ai.github.io/free-photo-to-scanned-pdf/)**

Turn document photos into one scanned PDF, directly in your browser. No installation, signup, email, card details, or payment required. Photos stay on your device and are not uploaded to a processing server.

## How to use

1. Choose your photos (up to 20 pages).
2. Review each page and adjust the crop corners if needed.
3. Use Up and Down in the Pages list to set the PDF page order.
4. Choose color, grayscale, or black-and-white and your paper size.
5. Preview the scan, then click Download PDF.

On phones, scroll sideways through the Pages list to see all photos. JPEG, PNG, WebP, and other supported browser image formats work; HEIC may need conversion to JPEG.

## Features and limits

- Automatic edge detection, adjustable perspective cropping, and rotation.
- Multiple photos combined into a single PDF, with page reordering.
- Color, grayscale, and black-and-white scans; A4, Letter, or fit-to-image pages.
- No paid backend, external libraries, or account requirement.

Review every page before sharing. Automatic cropping may need correction. PDFs contain scanned images, not searchable OCR text. Blurry, obscured, or missing text cannot be recovered. Limits: 20 photos, 30 MB per image, and 50 million pixels per image; working images are reduced to a maximum of 2400 pixels on the longest edge. Device memory limits still apply.

## Website source

GitHub Pages publishes the `docs/` folder:

- `index.html`: page content and controls.
- `style.css`: layout and appearance.
- `app.js`: image processing, cropping, ordering, and PDF creation.
- `.nojekyll`: static publishing configuration.

To preview locally, run `python3 -m http.server 8765 --directory docs` and open http://localhost:8765. Python is only used for this optional local preview; visitors need only a browser.

Older desktop and agent-plugin implementations have been removed from the current source tree. Earlier versions remain in Git history and existing releases.
