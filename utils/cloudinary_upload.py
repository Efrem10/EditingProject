import cloudinary.uploader


# ============================================================
# UPLOAD VIDEO TO CLOUDINARY
# ============================================================

def upload_video_to_cloudinary(file_path: str):

    result = cloudinary.uploader.upload_large(
        file_path,
        resource_type="video",
        folder="EditingPro/videos",
        chunk_size=6000000,  # 6 MB chunks
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

    return cloudinary.uploader.destroy(
        public_id,
        resource_type="video",
    )


# ============================================================
# UPLOAD COURSE THUMBNAIL / COVER IMAGE
# ============================================================

def upload_course_thumbnail_to_cloudinary(file_path: str):

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
# DELETE COURSE THUMBNAIL / COVER IMAGE
# ============================================================

def delete_course_thumbnail_from_cloudinary(public_id: str):

    return cloudinary.uploader.destroy(
        public_id,
        resource_type="image",
    )