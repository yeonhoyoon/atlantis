import random
from datetime import datetime, timedelta
from exceptions import NotImplementedError
from google.appengine.ext import db
from webapp2_extras import auth, security
import keys
from util import util
import logging

class UserToken(db.Model):
    created = db.DateTimeProperty(auto_now_add=True)
    updated = db.DateTimeProperty(auto_now=True)
    username = db.StringProperty(required=True, indexed=False)
    subject = db.StringProperty(required=True)
    token = db.StringProperty(required=True)

    @classmethod
    def get_key(cls, username, subject, token):
        return db.Key.from_path('UserToken', 
                                '%s.%s.%s' % (str(username), subject, token)).name()

    @classmethod
    def create(cls, username, subject, token=None):
        token = token or security.generate_random_string(entropy=128)
        key = cls.get_key(username, subject, token)
        entity = cls(key_name=key, username=username, subject=subject, token=token)
        entity.put()
        return entity

    @classmethod
    def get(cls, username, subject=None, token=None):
        if username and subject and token:
            return cls.get_by_key_name(cls.get_key(username, subject, token))

        assert subject and token, \
            'subject and token must be provided to UserToken.get().'

        return cls.all().filter('subject =', subject).filter('token =', token).get()


class UserState:
    NOT_AUTH = 'NOT_AUTH'
    NO_PERSONAL_INFO = 'NO_PERSONAL_INFO' 
    NO_PROFILE = 'NO_PROFILE'
    INACTIVE = 'INACTIVE'
    SHOW_ALL = 'SHOW_ALL'
    SHOW_SUMMARY = 'SHOW_SUMMARY'
    SHOW_PROFILE = 'SHOW_PROFILE'
    PROPOSED = 'PROPOSED'
    MATCHED = 'MATCHED'
    COUPLED = 'COUPLED'


class User(db.Model):
    username = db.StringProperty(required=True)
    password = db.StringProperty(required=True)
    last_active = db.DateTimeProperty(required=True, auto_now=True)
    created = db.DateTimeProperty(required=True, auto_now_add=True)

    name = db.StringProperty()
    phone = db.PhoneNumberProperty()
    gender = db.CategoryProperty(choices=set(['M', 'F']))
    contact_allowed_gender = db.CategoryProperty(choices=set(['M', 'F', 'MF']))
    birth_year = db.IntegerProperty()
    region = db.CategoryProperty()
    nickname = db.StringProperty()
    tags = db.StringListProperty()
    profile = db.TextProperty()
    profile_uuid = db.StringProperty()
    
    state = db.CategoryProperty(required=True, default=UserState.NOT_AUTH,
                                choices=set([UserState.NOT_AUTH, UserState.INACTIVE,
                                             UserState.NO_PERSONAL_INFO, UserState.NO_PROFILE,
                                             UserState.SHOW_ALL, UserState.SHOW_SUMMARY, UserState.SHOW_PROFILE,
                                             UserState.PROPOSED, UserState.MATCHED, UserState.COUPLED]))
    state_changed = db.DateTimeProperty(required=True, auto_now_add=True)
    selected_profile_uuids = db.StringListProperty()

    @classmethod
    def create_user(cls, username, raw_password):
        user = User(key_name=username, username=username, 
                    password=security.generate_password_hash(raw_password, length=12))
        user.put()
        return user

    def set_password(self, raw_password):
        self.password = security.generate_password_hash(raw_password, length=12)

    @classmethod
    def get_by_username(cls, username):
        user = cls.all().filter('username =', username).get()
        return user

    def get_id(self):
        return self.username

    @classmethod
    def get_by_auth_password(cls, username, password):
        user = cls.get_by_username(username)
        if not user:
            raise auth.InvalidAuthIdError()

        if not security.check_password_hash(password, user.password):
            raise auth.InvalidPasswordError()

        return user

    @classmethod
    def get_by_auth_token(cls, username, token):
        raise NotImplementedError

    @classmethod
    def create_auth_token(cls, username):
        return UserToken.create(username, 'auth').token

    @classmethod
    def delete_auth_token(cls, username, token):
        UserToken.get(username, 'auth', token).delete()

    @classmethod
    def create_signup_token(cls, username):
        entity = UserToken.create(username, 'signup')
        return entity.token

    @classmethod
    def validate_signup_token(cls, username, token):
        return UserToken.get(username, 'signup', token) is not None

    @classmethod
    def delete_signup_token(cls, username, token):
        UserToken.get(username, 'signup', token).delete()

    @classmethod
    def by_profile_uuids(cls, profile_uuids):
        users = cls.all().filter('profile_uuid IN', profile_uuids).run()
        return users

    @classmethod
    def get_recent_users(cls):
        q = cls.all()
        q.filter('last_active >', datetime.utcnow() - timedelta(days=3))
        recent_users = q.run()
        return recent_users

    def get_random_profile_lines(self):
        profile_lines = util.tokenize_sentences(self.profile)    
        random.seed(keys.RANDOM_SEED + datetime.today().toordinal())    
        random_profile_lines = random.sample(util.pad(profile_lines, '', 3), 3)
        random_profile_lines = [util.shorten_if_long(l) for l in random_profile_lines]
        return random_profile_lines

    def update_state(self):
        self.put()
        # if self.state == UserState.NOT_AUTH:
        #     pass
        # else:
        #     if not (self.nickname and self.tags and self.profile):
        #         self.state = UserState.NO_PROFILE
        #     elif not (self.name and self.phone):
        #         self.state = UserState.NO_PERSONAL_INFO
        #     else:
        #         self.state = UserState.SHOW_ALL

        #     self.state_changed = datetime.now()
        #     self.put()


class Proposal(db.Model):
    from_user = db.ReferenceProperty(reference_class=User, required=True,
                                     collection_name='sent_proposals')
    to_user = db.ReferenceProperty(reference_class=User, required=True,
                                   collection_name='received_proposals')
    created = db.DateTimeProperty(required=True)
    is_active = db.BooleanProperty(required=True)
    is_accepted = db.BooleanProperty(required=True)
