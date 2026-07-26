import cloudinary.uploader

def upload_video_to_cloudinary(file_path: str):
   
    result = cloudinary.uploader.upload_large(
        file_path,
        resource_type="video",
        folder="EditingPro/videos",
        chunk_size=6000000  # 6 MB chunks
    )
   
    return {
        "public_id": result["public_id"],
        "secure_url": result["secure_url"],
        "duration": result.get("duration"),
        "format": result.get("format")
    }


def delete_video_from_cloudinary(public_id: str):
    return cloudinary.uploader.destroy(
        public_id,
        resource_type="video"
    )    