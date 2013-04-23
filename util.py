import re
import hmac
from library.pybcrypt import bcrypt
import keys

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

def pad(l, content, width):
    l.extend([content] * (width - len(l)))
    return l

sentence_separators = re.compile(r'(?:(?<=[.!?]))|[\n]')

def tokenize_sentences(text):
    return filter(lambda s: s, map(lambda s: s.strip(), sentence_separators.split(text)))

def shorten_if_long(sentence):
    #return str(type(sentence))
    #for i in range(10):

    if len(sentence) > 45:
        return sentence[:45].strip() + '...'
    else:
        return sentence

