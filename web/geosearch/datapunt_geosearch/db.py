import contextlib
import functools
import logging

import psycopg2.extras
from psycopg2 import Error as Psycopg2Error


_logger = logging.getLogger(__name__)


def retry_on_psycopg2_error(func):
    """
    Decorator that retries 3 times after Postgres error, in particular if
    the connection was not valid anymore because the database was restarted
    """
    @functools.wraps(func)
    def wrapper_retry(*args, **kwargs):
        retry = 3
        while retry > 0:
            try:
                result = func(*args, **kwargs)
            except Psycopg2Error:
                if retry == 0:
                    raise
                else:
                    retry -= 1
                    _logger.warning(f'Retry query for {func.__name__} ({retry})')
                    continue
            break
        return result
    return wrapper_retry


@functools.lru_cache()
def dbconnection(dsn):
    """Creates an instance of _DBConnection and remembers the last one made."""
    return _DBConnection(dsn)


class _DBConnection:
    """ Wraps a PostgreSQL database connection that reports crashes and tries
    its best to repair broken connections.

    NOTE: doesn't always work, but the failure scenario is very hard to
      reproduce. Also see https://github.com/psycopg/psycopg2/issues/263
    """

    def __init__(self, *args, **kwargs):
        self.conn_args = args
        self.conn_kwargs = kwargs
        self._conn = None
        self._connect()

    def _connect(self):
        if self._conn is None:
            self._conn = psycopg2.connect(*self.conn_args, **self.conn_kwargs)
            self._conn.autocommit = True

    def _is_usable(self):
        """ Checks whether the connection is usable.

        :returns boolean: True if we can query the database, False otherwise
        """
        try:
            self._conn.cursor().execute("SELECT 1")
        except psycopg2.Error:
            return False
        else:
            return True

    @contextlib.contextmanager
    def _connection(self):
        """ Contextmanager that catches tries to ensure we have a database
        connection. Yields a Connection object.

        If a :class:`psycopg2.DatabaseError` occurs then it will check whether
        the connection is still usable, and if it's not, close and remove it.
        """
        try:
            self._connect()
            yield self._conn
        except psycopg2.Error as e:
            _logger.critical('AUTHZ DatabaseError: {}'.format(e))
            if not self._is_usable():
                with contextlib.suppress(psycopg2.Error):
                    self._conn.close()
                self._conn = None
            raise e

    @contextlib.contextmanager
    def transaction_cursor(self, cursor_factory=None):
        """ Yields a cursor with transaction.
        """
        with self._connection() as transaction:
            with transaction:
                with transaction.cursor(cursor_factory=cursor_factory) as cur:
                    yield cur

    @contextlib.contextmanager
    def cursor(self, cursor_factory=None):
        """ Yields a cursor without transaction.
        """
        with self._connection() as conn:
            with conn.cursor(cursor_factory=cursor_factory) as cur:
                yield cur

    def fetch_dict(self, sql):
        with self._connection() as conn:
            with conn.cursor(
                    cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(sql)
                return cur.fetchall()

    def fetch_one(self, sql):
        with self._connection() as conn:
            with conn.cursor(
                    cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(sql)
                return cur.fetchone()
