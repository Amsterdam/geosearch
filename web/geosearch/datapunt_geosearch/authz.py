import functools
import json
import logging
import re
import requests

from jwcrypto.jwk import JWKSet
from jwcrypto.jwt import JWT, JWTMissingKey
from jwcrypto.common import JWException
from flask import request as flask_request
from flask import current_app
from flask import abort
from flask import g

logger = logging.getLogger(__name__)


def authenticate(func):
    """
    Perform authentication check.
    In case JWT token in present in request: update request with `auth` spec.
    """
    @functools.wraps(func)
    def wrapper():
        print('-' * 80)  # TODO: removeme
        check_authentication(request=flask_request)
        return func()
    return wrapper


def check_authentication(request):
    token = get_token_from_request(request=request)
    jwks_url = current_app.config.get("JWKS_URL")
    if token is not None and jwks_url is not None:
        keyset = JWKSet()
        load_jwks(keyset=keyset)
        load_jwks_from_url(keyset=keyset, jwks_url=jwks_url)
        try:
            jwt = JWT(jwt=token,
                      key=keyset,
                      algs=current_app.config.get("JWKS_SIGNING_ALGORITHMS"))
        except JWTMissingKey as e:
            logger.warning('Auth problem: unknown key. {}'.format(e))
            abort(401, "Incorrect Bearer.")

        claims = get_claims(jwt)
        if claims:
            g.auth_scopes = claims['scopes']
    return None


def get_token_from_request(request):
    authorization_header = request.headers.get('Authorization', None)
    if authorization_header is not None:
        match = re.fullmatch(r'bearer ([-\w.=]+)',
                             authorization_header,
                             flags=re.IGNORECASE)
        if match:
            return match[1]
    return None


def get_claims(jwt):
    claims = json.loads(jwt.claims)
    if 'scopes' in claims:
        # Authz token structure
        return {
            'sub': claims.get('sub'),
            'scopes': set(claims['scopes'])
        }
    elif claims.get('realm_access'):
        # Keycloak token structure
        return {
            'sub': claims.get('sub'),
            'scopes': {
                convert_scope(r) for r in claims['realm_access']['roles']
            }
        }
    return None


def load_jwks(keyset):
    jwks = current_app.config.get('JWKS')
    if jwks:
        keyset.import_keyset(json.dumps(jwks))


def load_jwks_from_url(keyset, jwks_url):
    try:
        response = requests.get(jwks_url)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        raise Exception(  # TODO: Add proper exception
            "Failed to get JWKS from url: {}, error: {}".format(jwks_url, e)
        )
    try:
        keyset.import_keyset(response.text)
    except JWException as e:
        pass
    logger.info('Loaded JWKS from JWKS_URL setting {}'.format(jwks_url))


def convert_scope(scope):
    """ Convert Keycloak role to authz style scope
    """
    return scope.upper().replace("_", "/")
