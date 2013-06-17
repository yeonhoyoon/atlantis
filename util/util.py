import re
import hmac
from datetime import datetime, timedelta
from library.pybcrypt import bcrypt
import keys
import webapp2
from webapp2_extras import sessions, auth
import xsrf

COOKIE_SEPARATOR = '|'


def make_cookie_value(value):
        hashed = hmac.new(keys.COOKIE_SECRET, str(value)).hexdigest()
        return '{0}{1}{2}'.format(value, COOKIE_SEPARATOR, hashed)

def check_cookie_value(cookie_value):
    value, hashed = cookie_value.split(COOKIE_SEPARATOR)
    if make_cookie_value(value) == cookie_value:
        return value

def make_password_hash(password):
    return bcrypt.hashpw(password, bcrypt.gensalt())

def check_password(password, hashed):
    return bcrypt.hashpw(password, hashed) == hashed

def set_secure_cookie(response, name, value):
    cookie_value = make_cookie_value(value)
    response.headers.add_header(
        'Set-Cookie', 
        '{0}={1}; Path=/; HttpOnly'.format(name, cookie_value))

def read_secure_cookie(request, name):
    cookie_value = request.cookies.get(name)
    return cookie_value and check_cookie_value(cookie_value)

def pad(l, content, width):
    l.extend([content] * (width - len(l)))
    return l

sentence_separators = re.compile(r'(?:(?<=[.!?]))|[\n]')

def tokenize_sentences(text):
    return filter(lambda s: s, map(lambda s: s.strip(), sentence_separators.split(text)))

def shorten_if_long(sentence):
    if len(sentence) > 45:
        return sentence[:45].strip() + '...'
    else:
        return sentence

def get_display_time(utctime):
    utctime = utctime - timedelta(microseconds=utctime.microsecond)
    return utctime + timedelta(hours=9)