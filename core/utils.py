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
        print("DEBUG compress_image: No image provided")
        return image

    try:
        print(f"DEBUG compress_image: Starting compression of {image.name}, size={image.size} bytes = {image.size/1024/1024:.2f}MB")

        # Reset file pointer to beginning
        image.seek(0)

        # Open image with Pillow
        img = Image.open(image)
        img.load()  # Force load the image data

        print(f"DEBUG compress_image: Image opened, mode={img.mode}, size={img.size}")

        # Convert to RGB if needed
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

        max_size_bytes = max_size_mb * 1024 * 1024
        print(f"DEBUG compress_image: Target size = {max_size_mb}MB = {max_size_bytes} bytes")

        output = io.BytesIO()
        img.save(output, format='JPEG', quality=quality, optimize=True)
        current_size = output.tell()
        print(f"DEBUG compress_image: After first save, size={current_size} bytes = {current_size/1024/1024:.2f}MB")

        # Reduce quality progressively
        while current_size > max_size_bytes and quality > 20:
            quality -= 10
            output = io.BytesIO()
            img.save(output, format='JPEG', quality=quality, optimize=True)
            current_size = output.tell()
            print(f"DEBUG compress_image: quality={quality}, size={current_size/1024/1024:.2f}MB")

        # Resize if still too large
        if current_size > max_size_bytes:
            width, height = img.size
            while current_size > max_size_bytes and width > 100:
                width = int(width * 0.9)
                height = int(height * 0.9)
                img_resized = img.resize((width, height), Image.LANCZOS)
                output = io.BytesIO()
                img_resized.save(output, format='JPEG', quality=quality, optimize=True)
                current_size = output.tell()
                print(f"DEBUG compress_image: resized to {width}x{height}, size={current_size/1024/1024:.2f}MB")

        output.seek(0)
        final_size = output.getbuffer().nbytes
        print(f"DEBUG compress_image: FINAL size={final_size} bytes = {final_size/1024/1024:.2f}MB")

        return InMemoryUploadedFile(
            output,
            'ImageField',
            new_name,
            'image/jpeg',
            final_size,
            None
        )

    except Exception as e:
        print(f"DEBUG compress_image: ERROR - {str(e)}")
        import traceback
        traceback.print_exc()
        # Return original image if compression fails
        image.seek(0)
        return image
