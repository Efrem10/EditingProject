import firebase_admin
from firebase_admin import credentials
import os
import json


if not firebase_admin._apps:

    firebase_json = os.environ.get(
        "FIREBASE_SERVICE_ACCOUNT"
    )

    if firebase_json:
        cred = credentials.Certificate(
            json.loads(firebase_json)
        )

        firebase_admin.initialize_app(cred)

    else:
        raise Exception(
            "FIREBASE_SERVICE_ACCOUNT environment variable is missing"
        )