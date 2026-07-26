import cloudinary

from config import (
    CLOUDINARY_CLOUD_NAME,
    CLOUDINARY_API_KEY,
    CLOUDINARY_API_SECRET,
)
print("Cloud Name:", CLOUDINARY_CLOUD_NAME)
print("API Key:", CLOUDINARY_API_KEY)
print("API Secret Length:", len(CLOUDINARY_API_SECRET) if CLOUDINARY_API_SECRET else None)

cloudinary.config(
    cloud_name=CLOUDINARY_CLOUD_NAME,
    api_key=CLOUDINARY_API_KEY,
    api_secret=CLOUDINARY_API_SECRET,
    secure=True,
)