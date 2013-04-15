import hmac
from lib.pybcrypt import bcrypt

COOKIE_SECRET = '401b09eab3c013d4ca54922bb802bec8' #move to another file.
COOKIE_SEPARATOR = '|'

def make_cookie_value(value):
        hashed = hmac.new(COOKIE_SECRET, str(value)).hexdigest()
        return '{0}{1}{2}'.format(value, COOKIE_SEPARATOR, hashed)

def check_cookie_value(cookie_value):
    value, hashed = cookie_value.split(COOKIE_SEPARATOR)
    if make_cookie_value(value) == cookie_value:
        return value

def make_password_hash(password):
    return bcrypt.hashpw(password, bcrypt.gensalt())

def check_password(password, hashed):
    return bcrypt.hashpw(password, hashed) == hashed