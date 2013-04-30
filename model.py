import random
from datetime import datetime, timedelta
import time
from exceptions import NotImplementedError
from google.appengine.ext import ndb
from webapp2_extras import auth, security
import keys
from util import util
import logging

class UserToken(ndb.Model):
    created = ndb.DateTimeProperty(auto_now_add=True)
    updated = ndb.DateTimeProperty(auto_now=True)
    username = ndb.StringProperty(required=True, indexed=False)
    subject = ndb.StringProperty(required=True)
    token = ndb.StringProperty(required=True)

    @classmethod
    def get_key(cls, username, subject, token):
        return ndb.Key(cls, '%s.%s.%s' % (str(username), subject, token))

    @classmethod
    def create(cls, username, subject, token=None):
        token = token or security.generate_random_string(entropy=128)
        key = cls.get_key(username, subject, token)
        entity = cls(key=key, username=username, subject=subject, token=token)
        entity.put()
        return entity

    @classmethod
    def get(cls, username, subject=None, token=None):
        if username and subject and token:
            return cls.get_key(username, subject, token).get()

        assert subject and token, \
            'subject and token must be provided to UserToken.get().'

        return cls.query(cls.subject == subject, cls.token == token).get()


class UserState:
    NO_PERSONAL_INFO = 'NO_PERSONAL_INFO' 
    NO_PROFILE = 'NO_PROFILE'
    SHOW_ALL = 'SHOW_ALL'
    SHOW_SUMMARY = 'SHOW_SUMMARY'
    SHOW_PROFILE = 'SHOW_PROFILE'
    PROPOSED = 'PROPOSED'
    MATCHED = 'MATCHED'
    COUPLED = 'COUPLED'


class User(ndb.Model):
    username = ndb.StringProperty(required=True)
    password = ndb.StringProperty(required=True)
    last_active = ndb.DateTimeProperty(required=True, auto_now=True)
    created = ndb.DateTimeProperty(required=True, auto_now_add=True)

    name = ndb.StringProperty()
    phone = ndb.StringProperty()
    gender = ndb.StringProperty(choices=set(['M', 'F']))
    contact_allowed_gender = ndb.StringProperty(choices=set(['M', 'F', 'MF']))
    birth_year = ndb.IntegerProperty()
    region = ndb.StringProperty()
    nickname = ndb.StringProperty()
    tags = ndb.StringProperty(repeated=True)
    profile = ndb.TextProperty()
    profile_uuid = ndb.StringProperty()
    
    state = ndb.StringProperty(default=UserState.SHOW_ALL,
                               choices=set([UserState.NO_PERSONAL_INFO, UserState.NO_PROFILE,
                                            UserState.SHOW_ALL, UserState.SHOW_SUMMARY, UserState.SHOW_PROFILE,
                                            UserState.PROPOSED, UserState.MATCHED, UserState.COUPLED]))
    state_changed = ndb.DateTimeProperty(required=True, auto_now_add=True)
    selected_profile_uuids = ndb.StringProperty(repeated=True)
    verified = ndb.BooleanProperty(default=False)
    active = ndb.BooleanProperty(default=True)

    @classmethod
    def create_user(cls, username, raw_password):
        user = User(id=username, username=username, 
                    password=security.generate_password_hash(raw_password, length=12))
        user.put()
        return user

    def set_password(self, raw_password):
        self.password = security.generate_password_hash(raw_password, length=12)

    def get_id(self):
        return self._key.id()

    @classmethod
    def get_by_auth_password(cls, username, password):
        user = cls.get_by_id(username)
        if not user:
            raise auth.InvalidAuthIdError()

        if not security.check_password_hash(password, user.password):
            raise auth.InvalidPasswordError()

        return user

    @classmethod
    def get_by_auth_token(cls, username, token):
        token_key = UserToken.get_key(username, 'auth', token)
        user_key = ndb.Key(cls, username)
        # Use get_multi() to save a RPC call.
        valid_token, user = ndb.get_multi([token_key, user_key])
        if valid_token and user:
            timestamp = int(time.mktime(valid_token.created.timetuple()))
            return user, timestamp

        return None, None

    @classmethod
    def create_auth_token(cls, username):
        return UserToken.create(username, 'auth').token

    @classmethod
    def delete_auth_token(cls, username, token):
        UserToken.get_key(username, 'auth', token).delete()

    @classmethod
    def create_signup_token(cls, username):
        entity = UserToken.create(username, 'signup')
        return entity.token

    @classmethod
    def validate_signup_token(cls, username, token):
        return UserToken.get(username, 'signup', token) is not None

    @classmethod
    def delete_signup_token(cls, username, token):
        UserToken.get_key(username, 'signup', token).delete()

    @classmethod
    def by_profile_uuids(cls, profile_uuids):
        users = cls.query().filter(cls.profile_uuid.IN(profile_uuids)).iter()
        return users

    @classmethod
    def get_recent_users(cls):
        q = cls.query().filter(cls.last_active > datetime.utcnow() - timedelta(days=3))
        recent_users = q.iter()
        return recent_users

    def get_random_profile_lines(self):
        profile_lines = util.tokenize_sentences(self.profile)    
        random.seed(keys.RANDOM_SEED + datetime.today().toordinal())    
        random_profile_lines = random.sample(util.pad(profile_lines, '', 3), 3)
        random_profile_lines = [util.shorten_if_long(l) for l in random_profile_lines]
        return random_profile_lines

    def set_state(self, new_state):
        self.state = new_state
        self.state_changed = datetime.now()

    def _pre_put_hook(self):
        if not (self.name and self.phone):
            self.set_state(UserState.NO_PERSONAL_INFO)
        elif not (self.nickname and self.profile and not self.profile.isspace()):
            self.set_state(UserState.NO_PROFILE)
        elif self.state in [UserState.NO_PERSONAL_INFO, UserState.NO_PROFILE]:
            self.set_state(UserState.SHOW_ALL)


class Proposal(ndb.Model):
    from_user = ndb.KeyProperty(kind=User, required=True)
    to_user = ndb.KeyProperty(kind=User, required=True)
    created = ndb.DateTimeProperty(required=True)
    is_active = ndb.BooleanProperty(required=True)
    is_accepted = ndb.BooleanProperty(required=True)
