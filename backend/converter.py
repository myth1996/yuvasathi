import io
import logging
from PIL import Image, UnidentifiedImageError
import fitz  # PyMuPDF

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# DPI levels to try for PDF page rasterisation (high → low)
# Note: because pages are embedded as JPEG (not raw PNG), 72 DPI still looks
# much better than the old raw-rasterisation approach at the same DPI.
PDF_DPI_LEVELS = [200, 150, 120, 100, 85, 72]
# JPEG quality levels to try when embedding page images inside a PDF
PDF_JPEG_QUALITY = [85, 75, 65]
# JPEG quality levels for photo/signature images (never below 65 — keeps text legible)
IMAGE_JPEG_QUALITY = [85, 75, 65]
# Resize multipliers for images — only gentle reduction, 0.75 is the floor
IMAGE_RESIZE_STEPS = [1.0, 0.9, 0.75]
# Cap image longest side to this many pixels before any quality pass
IMAGE_MAX_DIMENSION = 1600


def compress_pdf(file_bytes: bytes, max_mb: float = 0.3) -> bytes:
    """
    Compresses a PDF to stay within max_mb (default 300 KB).

    Strategy:
    1. Try lossless garbage-collect + deflate — keeps text as crisp vectors.
    2. If still too large, rasterise each page as a JPEG (not raw PNG) and
       rebuild the PDF.  By embedding JPEG we can achieve much smaller sizes
       at higher DPI, so legibility is preserved.
    3. Works through (dpi, jpeg_quality) pairs from high to low, returning
       the first result that meets the size target.
    4. Returns the smallest version produced if the target is never met.
    """
    max_bytes = int(max_mb * 1024 * 1024)

    try:
        doc = fitz.open(stream=file_bytes, filetype="pdf")
    except fitz.errors.FitzError as e:
        logging.error(f"Failed to open PDF: {e}")
        return file_bytes

    # --- Step 1: lossless compression (no quality loss) ---
    logging.info("Step 1: lossless garbage-collect + deflate")
    lossless = doc.tobytes(garbage=4, deflate=True)
    if len(lossless) <= max_bytes:
        logging.info(f"Lossless pass sufficient: {len(lossless)/1024:.1f} KB")
        return lossless

    # --- Step 2: JPEG-inside-PDF rasterisation ---
    num_pages = len(doc)
    per_page_budget = max_bytes / num_pages
    logging.info(f"{num_pages} page(s), per-page budget: {per_page_budget/1024:.1f} KB")

    best = lossless  # keep track of smallest so far as fallback
    for dpi in PDF_DPI_LEVELS:
        for jpeg_quality in PDF_JPEG_QUALITY:
            logging.info(f"Trying {dpi} DPI, JPEG quality {jpeg_quality}")

            # Quick per-page estimate: render one page as JPEG and check size.
            # If a single page already exceeds the per-page budget, skip this
            # combination early rather than building the whole PDF.
            sample_pix = doc[0].get_pixmap(dpi=dpi, alpha=False)
            sample_jpeg = sample_pix.tobytes("jpeg", jpg_quality=jpeg_quality)
            if num_pages > 1 and len(sample_jpeg) > per_page_budget * 1.5:
                logging.info(f"  Skipping — sample page {len(sample_jpeg)/1024:.1f} KB > budget")
                continue

            new_doc = fitz.open()
            for page in doc:
                pix = page.get_pixmap(dpi=dpi, alpha=False)
                jpeg_bytes = pix.tobytes("jpeg", jpg_quality=jpeg_quality)
                img_pdf = fitz.open()
                img_page = img_pdf.new_page(width=pix.width, height=pix.height)
                img_page.insert_image(img_page.rect, stream=jpeg_bytes)
                new_doc.insert_pdf(img_pdf)
                img_pdf.close()

            result = new_doc.tobytes(garbage=4, deflate=True)
            new_doc.close()
            logging.info(f"  → {len(result)/1024:.1f} KB")

            if len(result) < len(best):
                best = result

            if len(result) <= max_bytes:
                logging.info(f"Target met at {dpi} DPI / Q{jpeg_quality}")
                return result

    logging.warning("Target size not met; returning smallest version produced.")
    return best


def compress_image(file_bytes: bytes, fmt: str = "JPEG", max_mb: float = 0.05) -> bytes:
    """
    Compresses a photo or signature to stay within max_mb (default 50 KB).

    Strategy:
    1. Cap the longest side to IMAGE_MAX_DIMENSION (1600 px) first — avoids
       needless quality loss on very large originals.
    2. Try progressively lower quality levels (JPEG: 85 → 75 → 65).
    3. If still too large, gently resize (90 % → 75 %) and repeat quality loop.
    4. Minimum JPEG quality is 65 — below that text in signatures becomes
       illegible; similarly the resize floor is 0.75 to preserve proportions.
    5. PNG signatures use lossless encoding but still benefit from capping
       dimensions and resizing.
    """
    max_bytes = int(max_mb * 1024 * 1024)

    try:
        img = Image.open(io.BytesIO(file_bytes))
    except (UnidentifiedImageError, IOError) as e:
        logging.error(f"Cannot open image: {e}")
        return file_bytes

    # Convert RGBA / palette images to RGB for JPEG compatibility
    if fmt.upper() == "JPEG" and img.mode in ("RGBA", "P"):
        img = img.convert("RGB")

    # --- Step 1: cap maximum dimension to avoid extreme quality penalties ---
    w, h = img.size
    longest = max(w, h)
    if longest > IMAGE_MAX_DIMENSION:
        scale = IMAGE_MAX_DIMENSION / longest
        img = img.resize((int(w * scale), int(h * scale)), Image.Resampling.LANCZOS)
        logging.info(f"Capped to {img.size} (was {w}×{h})")

    original_size = img.size

    # For PNG (signatures): lossless, so only the resize loop matters
    quality_steps = IMAGE_JPEG_QUALITY if fmt.upper() == "JPEG" else [None]

    # --- Step 2: quality × resize loops ---
    for resize_factor in IMAGE_RESIZE_STEPS:
        if resize_factor < 1.0:
            new_w = int(original_size[0] * resize_factor)
            new_h = int(original_size[1] * resize_factor)
            img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
            logging.info(f"Resized to {img.size}")

        for quality in quality_steps:
            output = io.BytesIO()
            save_kwargs: dict = {"format": fmt}
            if quality is not None:
                save_kwargs["quality"] = quality
                log_q = f"Q{quality}"
            else:
                log_q = "lossless"

            img.save(output, **save_kwargs)
            size_kb = output.tell() / 1024
            logging.info(f"  {resize_factor*100:.0f}% size, {log_q}: {size_kb:.1f} KB")

            if output.tell() <= max_bytes:
                logging.info(f"Target met: {size_kb:.1f} KB")
                return output.getvalue()

    logging.warning("Target size not met; returning smallest version produced.")
    output = io.BytesIO()
    img.save(output, format=fmt, **({"quality": IMAGE_JPEG_QUALITY[-1]} if fmt.upper() == "JPEG" else {}))
    return output.getvalue()
