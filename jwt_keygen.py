#!/usr/bin/env python
import argparse
import json
import pathlib
import sys
import time
import uuid

from jwcrypto.jwk import JWK
from jwcrypto.jwt import JWT

"""
Utitility script for generating JSON web keys and JSON web tokens
which can be used when testing geosearch. JWTs can contain private
claims which are scopes as used in the authorization mechanism of
amsterdam-schema.

The key used by the development configuration of Geosearch is stored in
test_jwk.json in the root folder of this repository.
"""

parser = argparse.ArgumentParser()
parser.add_argument("scopes", nargs="*", help="Scopes added to the JWT as private claims")
parser.add_argument("--exp", default=None, type=int, help="Number of seconds to expiration")

JWK_PATH = pathlib.Path(__file__).parent / "test_jwk.json"


def generate_jwk():
    return JWK.generate(kty="EC", crv="P-256", kid=str(uuid.uuid4()), key_ops=["verify", "sign"])


def generate_jwt(scopes, exp):
    """Generate a JWT, signed using the key stored at test_jwk.json.
    If there is no key at this location, generate it and write it to
    the file."""
    if JWK_PATH.exists():
        key = JWK(**json.load(open(JWK_PATH)))
    else:
        with open(JWK_PATH, "w+") as fp:
            key = generate_jwk()
            json.dump(key, fp, indent=2, sort_keys=True)

    scopes = list(set(scopes))
    now = int(time.time())
    claims = {
        "iat": now,
        "scopes": scopes,
        "sub": "test@amsterdam.nl",
    }
    if exp is not None:
        claims["exp"] = now + exp

    token = JWT(header={"alg": "ES256", "kid": key.kid}, claims=claims)
    token.make_signed_token(key)

    sys.stdout.write(token.serialize())
    sys.stdout.write("\n")


if __name__ == "__main__":
    args = parser.parse_args()
    generate_jwt(args.scopes, args.exp)
