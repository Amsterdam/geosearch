#!/usr/bin/env python3
# Usage: get-token.py scopes
import json
import sys
import time
from pathlib import Path

from jwcrypto.jwk import JWK
from jwcrypto.jwt import JWT

with Path(__file__).parent.joinpath("jwks_test.json").open() as f:
    key = JWK(**json.load(f)["keys"][0])

# Validity period, in seconds.
valid = 1800

scopes = sys.argv[1:]

now = int(time.time())
claims = {
    "iat": now,
    "exp": now + valid,
    "scopes": scopes,
    "sub": "test@tester.nl",
}
token = JWT(header={"alg": "ES256", "kid": key.key_id}, claims=claims)

token.make_signed_token(key)
print(token.serialize())
