import cloudinary
import cloudinary.uploader


# ============================================================
# UPLOAD VIDEO TO CLOUDINARY
# ============================================================

def upload_video_to_cloudinary(file_path: str):

    result = cloudinary.uploader.upload_large(
        file_path,
        resource_type="video",
        folder="EditingPro/videos",
        chunk_size=6_000_000,
    )

    return {
        "public_id": result["public_id"],
        "secure_url": result["secure_url"],
        "duration": result.get("duration"),
        "format": result.get("format"),
    }


# ============================================================
# DELETE VIDEO FROM CLOUDINARY
# ============================================================

def delete_video_from_cloudinary(public_id: str):

    if not public_id:
        return None

    return cloudinary.uploader.destroy(
        public_id,
        resource_type="video",
    )


# ============================================================
# UPLOAD COURSE THUMBNAIL / IMAGE
# ============================================================

def upload_image_to_cloudinary(file_path: str):

    result = cloudinary.uploader.upload(
        file_path,
        resource_type="image",
        folder="EditingPro/thumbnails",
    )

    return {
        "public_id": result["public_id"],
        "secure_url": result["secure_url"],
        "width": result.get("width"),
        "height": result.get("height"),
        "format": result.get("format"),
    }


# ============================================================
# DELETE COURSE THUMBNAIL / IMAGE
# ============================================================

def delete_image_from_cloudinary(public_id: str):

    if not public_id:
        return None

    return cloudinary.uploader.destroy(
        public_id,
        resource_type="image",
    )