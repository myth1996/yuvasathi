import io
from PIL import Image
import fitz

def compress_pdf(file_bytes, max_mb=0.3):  # 300KB
    max_bytes = int(max_mb * 1024 * 1024)
    doc = fitz.open(stream=file_bytes, filetype="pdf")
    
    for dpi in [150, 100, 72, 50, 36]:
        new_doc = fitz.open()
        for page in doc:
            mat = fitz.Matrix(dpi / 72, dpi / 72)
            pix = page.get_pixmap(matrix=mat)
            img_bytes = pix.tobytes("jpeg", jpg_quality=60)
            img_page = fitz.open()
            img_rect = fitz.Rect(0, 0, pix.width, pix.height)
            new_page = img_page.new_page(width=pix.width, height=pix.height)
            new_page.insert_image(img_rect, stream=img_bytes)
            new_doc.insert_pdf(img_page)
        result = new_doc.tobytes(deflate=True)
        if len(result) <= max_bytes:
            return result
    return result


def compress_image(file_bytes, fmt="JPEG", max_mb=0.05):  # 50KB
    max_bytes = int(max_mb * 1024 * 1024)
    img = Image.open(io.BytesIO(file_bytes))
    
    if fmt == "JPEG":
        img = img.convert("RGB")
    
    for quality in [85, 70, 55, 40, 25, 10]:
        output = io.BytesIO()
        save_kwargs = {"format": fmt}
        if fmt == "JPEG":
            save_kwargs["quality"] = quality
        img.save(output, **save_kwargs)
        if output.tell() <= max_bytes:
            return output.getvalue()
        w, h = img.size
        img = img.resize((int(w * 0.8), int(h * 0.8)), Image.LANCZOS)
    
    output = io.BytesIO()
    img.save(output, format=fmt)
    return output.getvalue()
