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


def get_current_authz_scopes():
    """
    Return current authz scopes.
    """
    return getattr(g, "authz_scopes", None)


def authenticate(func):
    """
    Perform authentication check.

    Optionally updates `g.authz_scopes` with scopes available for given token.
    Returns 401 in case token is invalid.
    """
    @functools.wraps(func)
    def wrapper():
        check_authentication(request=flask_request)
        return func()
    return wrapper


def check_authentication(request):
    """
    Optionally check authentication via on request.

    Returns None if request contains no Authorization header
     or header is correct.
    In case Authorization header is correct - updates `g.authz_scopes` with
     scopes from claims defined in JWT token.
    Aborts with 401 in case Authorization header contains incorrect token.
    """
    g.authz_scopes = None
    token = get_token_from_request(request=request)
    if token is not None:
        try:
            jwt = JWT(jwt=token,
                      key=current_app.config.get("JW_KEYSET"),
                      algs=current_app.config.get("JWKS_SIGNING_ALGORITHMS"))
        except JWTMissingKey as e:
            logger.warning('Auth problem: unknown key. {}'.format(e))
            abort(401, "Incorrect Bearer.")
        except ValueError as e:
            logger.warning('Auth problem: incorrect token. {}'.format(e))
            abort(401, "Incorrect Bearer.")

        claims = get_claims(jwt)
        if claims:
            g.authz_scopes = claims['scopes']
    return None


def get_token_from_request(request):
    """
    Parse request and get Auth token from it, if Authorization header is set.
    """
    authorization_header = request.headers.get('Authorization', None)
    if authorization_header is not None:
        match = re.fullmatch(r'bearer ([-\w.=]+)',
                             authorization_header,
                             flags=re.IGNORECASE)
        if match:
            return match[1]
    return None


def get_claims(jwt):
    """
    Parse jwt response and return scopes only.
    """
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


def get_keyset(jwks, jwks_url=None):
    """
    Initializes JWKSet instance with all the keys.
    """
    keyset = JWKSet()

    if jwks:
        keyset.import_keyset(jwks)
    if jwks_url:
        load_jwks_from_url(keyset=keyset, jwks_url=jwks_url)
    return keyset


def load_jwks_from_url(keyset, jwks_url):
    """
    Load JWKeys from URL.
    """
    try:
        response = requests.get(jwks_url)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        raise ValueError(
            "Failed to get JWKS from url: {}, error: {}".format(jwks_url, e)
        )
    try:
        keyset.import_keyset(response.text)
    except JWException as e:
        raise ValueError(
            "Failed to get JWKS from url: {}, error: {}".format(jwks_url, e)
        )
    else:
        logger.info('Loaded JWKS from JWKS_URL setting {}'.format(jwks_url))


def convert_scope(scope):
    """
    Convert Keycloak role to authz style scope
    """
    return scope.upper().replace("_", "/")
