import time
import json
import requests
from jwcrypto.jwt import JWT
from jwcrypto.jwk import JWKSet


JWKS = {
    "keys": [
        {
            "kty": "EC",
            "key_ops": [
                "verify",
                "sign"
            ],
            "kid": "2aedafba-8170-4064-b704-ce92b7c89cc6",
            "crv": "P-256",
            "x": "6r8PYwqfZbq_QzoMA4tzJJsYUIIXdeyPA27qTgEJCDw=",
            "y": "Cf2clfAfFuuCB06NMfIat9ultkMyrMQO9Hd2H7O9ZVE=",
            "d": "N1vu0UQUp0vLfaNeM0EDbl4quvvL6m_ltjoAXXzkI3U="
        }
    ]
}


def create_valid_token(subject, scopes):
    jwks = JWKSet()
    jwks.import_keyset(json.dumps(JWKS))

    assert len(jwks) > 0

    key = next(iter(jwks['keys']))
    now = int(time.time())

    header = {
        'alg': 'ES256',  # algorithm of the test key
        'kid': key.key_id
    }

    token = JWT(
        header=header,
        claims={
            'iat': now,
            'exp': now + 600,
            'scopes': scopes,
            'subject': subject
        })
    token.make_signed_token(key)
    return 'bearer ' + token.serialize()


def do_request(token):
    headers = None
    if token is not None:
        headers = dict(Authorization=token)
    return requests.get('http://localhost:8000/catalogus', headers=headers)


if __name__ == '__main__':
    response = do_request(None)

    assert "wegingen" not in response.json()['datasets']
    assert "asbestdaken" not in response.json()['datasets']

    response = do_request(
        token=create_valid_token(subject="test@test.nl", scopes=['TEST/R']))
    assert "wegingen" in response.json()['datasets']
    assert "asbestdaken" not in response.json()['datasets']

    response = do_request(
        token=create_valid_token(subject="test@test.nl", scopes=[
            'TEST/R',
            'TEST/W']))
    assert "wegingen" in response.json()['datasets']
    assert "asbestdaken" in response.json()['datasets']

    print("All tests passed.")
