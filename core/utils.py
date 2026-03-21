from PIL import Image
import io
import os
from django.core.files.uploadedfile import InMemoryUploadedFile


def compress_image(image, max_size_mb=1, quality=85):
    """
    Compress an uploaded image to under max_size_mb.
    Returns compressed image as InMemoryUploadedFile.
    """
    if not image:
        return image

    # Open image with Pillow
    img = Image.open(image)

    # Convert to RGB if needed (handles PNG with transparency)
    if img.mode in ('RGBA', 'P', 'LA'):
        background = Image.new('RGB', img.size, (255, 255, 255))
        if img.mode == 'RGBA':
            background.paste(img, mask=img.split()[3])
        else:
            background.paste(img)
        img = background
    elif img.mode != 'RGB':
        img = img.convert('RGB')

    # Get original file name
    original_name = os.path.splitext(image.name)[0]
    new_name = f"{original_name}.jpg"

    # Start with given quality and reduce until under max size
    max_size_bytes = max_size_mb * 1024 * 1024

    output = io.BytesIO()
    img.save(output, format='JPEG', quality=quality, optimize=True)

    # If still too large reduce quality progressively
    while output.tell() > max_size_bytes and quality > 20:
        quality -= 10
        output = io.BytesIO()
        img.save(output, format='JPEG', quality=quality, optimize=True)

    # Also resize if still too large
    if output.tell() > max_size_bytes:
        width, height = img.size
        while output.tell() > max_size_bytes and width > 100:
            width = int(width * 0.9)
            height = int(height * 0.9)
            img_resized = img.resize((width, height), Image.LANCZOS)
            output = io.BytesIO()
            img_resized.save(output, format='JPEG', quality=quality, optimize=True)

    output.seek(0)

    return InMemoryUploadedFile(
        output,
        'ImageField',
        new_name,
        'image/jpeg',
        output.getbuffer().nbytes,
        None
    )
