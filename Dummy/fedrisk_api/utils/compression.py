from PIL import Image
from fastapi import UploadFile
from io import BytesIO


async def compress_image(image: UploadFile, max_size_mb: int = 30, quality: int = 35):
    """
    Compress an image if its size is less than max_size_mb.

    :param image: UploadFile object containing the image.
    :param max_size_mb: Maximum file size in MB (default: 30MB) that is not rejected.
    :param quality: Quality for JPEG compression out of 100 (default: 35).
    :return: BytesIO object containing the compressed image.
    """

    content = await image.read()
    initial_size = len(content)

    max_size_bytes = max_size_mb * 1024 * 1024
    min_size_bytes = (1024 * 1024) / 5  # .2MB
    if initial_size > max_size_bytes:
        raise ValueError(
            f"File size too large ({initial_size / (1024 * 1024):.2f}MB). Maximum allowed: {max_size_mb}MB"
        )
    elif initial_size < min_size_bytes:
        print(f"Image size within limit ({initial_size * (1024 * 1024):.2f}MB)")
        return content, image.filename

    # Open the image
    img = Image.open(BytesIO(content))

    # If it's not JPEG, convert to JPEG for better compression
    if img.format != "JPEG":
        img = img.convert("RGB")

    output_io = BytesIO()
    img.save(output_io, format="JPEG", quality=quality)
    # Convert the BytesIO object back to an image

    # img.save(output_io, format='PNG', quality=quality)
    compressed_image_data = output_io.getvalue()

    print(f"Image compressed. New size: {len(compressed_image_data) / (1024 * 1024):.2f}MB")

    # output_io.seek(0)
    # return output_io
    return compressed_image_data
