import json
from base64 import b64encode

LABEL_STUDIO_VERIFIED_JWT = 'devstudio-verified-jwt'

def jwt_header(owner):
    jwt = {
        "gcip": {
            "email": owner,
            "email_verified": True,
            "teknoir": {
                "role": 'editor',
            },
        },
    }
    return {LABEL_STUDIO_VERIFIED_JWT: b64encode(json.dumps(jwt).encode('utf-8')).decode('utf-8')}