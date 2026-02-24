import io
import logging
from PIL import Image, UnidentifiedImageError
import fitz  # PyMuPDF

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Configuration Constants ---
PDF_DPI_LEVELS = [150, 100, 72]  # DPI levels to attempt for PDF compression
JPEG_QUALITY_LEVELS = [85, 75, 65, 50] # Quality levels for JPEG
IMAGE_RESIZE_STEPS = [1.0, 0.8, 0.6] # Resize multipliers for images (1.0 = original size)

def compress_pdf(file_bytes: bytes, max_mb: float = 0.3) -> bytes:
    """
    Compresses a PDF by converting its pages to JPEG images at decreasing DPIs.
    Returns the first version that is under the size limit.
    """
    max_bytes = int(max_mb * 1024 * 1024)
    
    try:
        doc = fitz.open(stream=file_bytes, filetype="pdf")
    except fitz.errors.FitzError as e:
        logging.error(f"Failed to open PDF stream: {e}")
        return file_bytes # Return original bytes if it's not a valid PDF

    # Try to save with garbage collection and deflation first
    logging.info("Attempting initial compression with garbage collection.")
    initial_compressed = doc.tobytes(garbage=4, deflate=True)
    if len(initial_compressed) <= max_bytes:
        logging.info(f"Initial compression successful. Size: {len(initial_compressed) / 1024:.1f} KB")
        return initial_compressed

    # If still too large, begin iterative image conversion
    for dpi in PDF_DPI_LEVELS:
        logging.info(f"Attempting PDF compression at {dpi} DPI...")
        new_doc = fitz.open()
        for page in doc:
            # Render page to a pixmap (an image)
            pix = page.get_pixmap(dpi=dpi, alpha=False)
            
            # Create a new 1-page PDF for the image
            img_page_pdf = fitz.open()
            img_page = img_page_pdf.new_page(width=pix.width, height=pix.height)
            img_page.insert_image(img_page.rect, pixmap=pix)
            
            # Insert this new page into our result document
            new_doc.insert_pdf(img_page_pdf)
            img_page_pdf.close()

        # Save the reconstructed PDF with compression
        result_bytes = new_doc.tobytes(garbage=4, deflate=True)
        new_doc.close()
        
        logging.info(f"Size at {dpi} DPI: {len(result_bytes) / 1024:.1f} KB")
        if len(result_bytes) <= max_bytes:
            logging.info(f"Target size met at {dpi} DPI. Final size: {len(result_bytes) / 1024:.1f} KB")
            return result_bytes
            
    logging.warning("Could not meet target size, returning the smallest version.")
    return result_bytes


def compress_image(file_bytes: bytes, fmt: str = "JPEG", max_mb: float = 0.05) -> bytes:
    """
    Compresses an image by iterating through quality and resize steps.
    """
    max_bytes = int(max_mb * 1024 * 1024)

    try:
        img = Image.open(io.BytesIO(file_bytes))
    except (UnidentifiedImageError, IOError) as e:
        logging.error(f"Cannot identify image file: {e}")
        return file_bytes

    # Ensure transparency is handled correctly for JPEG
    if fmt.upper() == "JPEG" and img.mode in ("RGBA", "P"):
        img = img.convert("RGB")
    
    original_size = img.size

    # Outer loop for resizing
    for resize_factor in IMAGE_RESIZE_STEPS:
        current_width = int(original_size[0] * resize_factor)
        current_height = int(original_size[1] * resize_factor)
        
        # Only resize if it's not the first (1.0) iteration
        if resize_factor < 1.0:
            logging.info(f"Resizing image to {current_width}x{current_height}")
            img = img.resize((current_width, current_height), Image.Resampling.LANCZOS)

        # Inner loop for quality
        quality_steps = JPEG_QUALITY_LEVELS if fmt.upper() == "JPEG" else [100] # PNG is lossless, quality is irrelevant
        for quality in quality_steps:
            output = io.BytesIO()
            save_kwargs = {"format": fmt}
            if fmt.upper() == "JPEG":
                save_kwargs["quality"] = quality
            
            logging.info(f"Attempting save with size={resize_factor*100}% and quality={quality}")
            img.save(output, **save_kwargs)
            
            if output.tell() <= max_bytes:
                logging.info(f"Target size met. Final size: {output.tell() / 1024:.1f} KB")
                return output.getvalue()

    logging.warning("Could not meet target size, returning the smallest version produced.")
    # Fallback to returning the last (smallest) generated version
    output = io.BytesIO()
    img.save(output, format=fmt)
    return output.getvalue()
