import cloudinary
import cloudinary.uploader

cloudinary.config(
    cloud_name="sdkw2hg2",
    api_key="531967922398637",
    api_secret="fQDuefX-BX9yUXdewToLQiI49H4",
    secure=True
)

result = cloudinary.uploader.upload(
    "test.jpg",
    folder="test"
)

print(result)

