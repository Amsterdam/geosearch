import time

from authorization_django.jwks import JWKSWrapper
from jwcrypto.jwt import JWT


def build_jwt_token(
    scopes, subject="text@example.com", expiration=30, aud="audience", iss="issuer"
):
    now = int(time.time())

    kid = "2aedafba-8170-4064-b704-ce92b7c89cc6"
    jwks = JWKSWrapper()
    key = jwks.keyset.get_key(kid)
    token = JWT(
        header={"alg": "ES256", "kid": kid},
        claims={
            "iat": now,
            "exp": now + expiration,
            "scopes": scopes,
            "sub": subject,
            "aud": aud,
            "iss": iss,
        },
    )
    token.make_signed_token(key)
    return token.serialize()
