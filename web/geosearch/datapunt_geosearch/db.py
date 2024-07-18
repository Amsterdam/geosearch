import contextlib
import functools
import logging

import psycopg2.extras
from cachetools import LRUCache, cached
from flask import current_app as app
from flask import g
from psycopg2 import Error as Psycopg2Error

_logger = logging.getLogger(__name__)

USER_ROLE = "{user_email}_role"
INTERNAL_ROLE = "medewerker_role"
ANONYMOUS_ROLE = "anonymous_role"
ANONYMOUS_APP_NAME = "geosearch-openbaar"


def is_internal(user_email: str) -> bool:
    """Tell whether a user is an internal user."""
    return user_email.endswith("@amsterdam.nl") or user_email.endswith("@ggd.amsterdam.nl")

def retry_on_psycopg2_error(func):
    """
    Decorator that retries 3 times after Postgres error, in particular if
    the connection was not valid anymore because the database was restarted
    """

    @functools.wraps(func)
    def wrapper_retry(*args, **kwargs):
        retry = 0
        while retry < 4:
            try:
                result = func(*args, **kwargs)
            except Psycopg2Error:
                retry += 1
                if retry > 3:
                    raise
                else:
                    _logger.warning(f"Retry query for {func.__name__} ({retry})")
                    continue
            break
        return result

    return wrapper_retry


connection_cache = LRUCache(maxsize=128)


@cached(cache=connection_cache)
def dbconnection(dsn, set_user_role=False):
    """Creates and caches instances of _DBConnection by DSN"""
    return _DBConnection(dsn, set_user_role)


class _DBConnection:
    """A PostgresQL database connection that
        - reports crashes
        - tries its best to repair broken connections
        - optionally switches the user-role using SET ROLE

    NOTE: doesn't always work, but the failure scenario is very hard to
      reproduce. Also see https://github.com/psycopg/psycopg2/issues/263
    """

    def __init__(self, dsn, set_user_role):
        self.set_user_role = set_user_role
        self.dsn = dsn
        self._conn = None
        self._active_user = None
        self._connect()

    def _connect(self):
        if self._conn is None:
            self._conn = psycopg2.connect(self.dsn)
            # Cursors will not run inside their own transactions
            self._conn.autocommit = True

    def _is_usable(self):
        """Checks whether the connection is usable.

        :returns boolean: True if we can query the database, False otherwise
        """
        try:
            self._conn.cursor().execute("SELECT 1")
        except Psycopg2Error:
            return False
        else:
            return True

    def activate_end_user(self):
        """Switch to the end-user role in the database."""
        if not app.config["DATABASE_SET_ROLE"] or not self.set_user_role:
            _logger.debug(
                "End-user feature disabled (DATABASE_SET_ROLE=%s, set_user_role=%s)",
                app.config["DATABASE_SET_ROLE"],
                self.set_user_role,
            )
            return

        user_email = g.get("email")
        if not user_email:
            _logger.debug("No end-user email, switching to anonymous role")
            self._set_role(ANONYMOUS_ROLE, ANONYMOUS_APP_NAME)
            return

        if self._active_user == user_email:
            _logger.debug("End-user already set, no need to switch roles again")
            return

        _logger.debug("%s: Activating end-user context for %s", user_email)

        role_name = USER_ROLE.format(user_email=user_email)
        if is_internal(user_email):
            # BBN1: Internal employee, no specific account
            self._set_role(INTERNAL_ROLE, user_email)
        else:
            _logger.exception("External user %s has no database role %s", user_email, role_name)
            raise PermissionError(f"User {user_email} is not available in database")

    def _set_role(self, role_name, app_name):
        # By starting a transaction, any connection pooling (e.g. PgBouncer)
        # can also ensure the connection is not reused for another session.
        with self._connection() as conn:
            with conn.cursor() as c:
                try:
                    c.execute(
                        "BEGIN; SET LOCAL ROLE %s; set application_name to %s;",
                        (role_name, app_name),
                    )
                except Psycopg2Error as e:
                    _logger.debug("Switch role failed for %s: %s", role_name, e)
                    c.execute("ROLLBACK;")
                    raise

                self._active_user = role_name
                _logger.debug(
                    "Activated end-user database role '%s' for '%s'",
                    role_name,
                    app_name,
                )

    def deactivate_end_user(self):
        """Rollback the transaction when the local user was activated."""
        if not self._active_user:
            _logger.debug("Not rolling back end-user since there is no active user")

        _logger.debug("End-user rollback for %s", self._active_user)
        try:
            with self._conn.cursor() as c:
                c.execute("ROLLBACK;")
            self._active_user = None
            g.email = None
        except Psycopg2Error as e:
            _logger.debug("Unable to rollback end user context for: %s", self._active_user)
            _logger.debug("Database error %s", e)

    @contextlib.contextmanager
    def _connection(self):
        """Contextmanager that catches tries to ensure we have a database
        connection. Yields a Connection object.

        If a :class:`psycopg2.DatabaseError` occurs then it will check whether
        the connection is still usable, and if it's not, close and remove it.
        """
        try:
            self._connect()
            yield self._conn
        except Psycopg2Error as e:
            _logger.critical("AUTHZ DatabaseError: {}".format(e))
            if self._conn is not None and not self._is_usable():
                with contextlib.suppress(psycopg2.Error):
                    self._conn.close()
                self._conn = None
            raise e

    @contextlib.contextmanager
    def cursor(self, cursor_factory=None):
        """Yields a cursor without transaction."""
        self.activate_end_user()
        with self._connection() as conn:
            with conn.cursor(cursor_factory=cursor_factory) as cur:
                yield cur

    def fetch_all(self, sql):
        with self.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql)
            return cur.fetchall()

    def fetch_one(self, sql):
        with self.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql)
            return cur.fetchone()
