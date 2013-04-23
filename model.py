import random
from datetime import datetime, timedelta
from google.appengine.ext import db
import keys
import util


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
    def by_username(cls, username):
        user = cls.all().filter('username =', username).get()
        return user

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

    @classmethod
    def validate(cls, name, password):
        user = cls.by_username(name)
        if user and util.check_password(password, user.password):
            return user

    def get_random_profile_lines(self):
        profile_lines = util.tokenize_sentences(self.profile)    
        random.seed(keys.RANDOM_SEED + datetime.today().toordinal())    
        random_profile_lines = random.sample(util.pad(profile_lines, '', 3), 3)
        random_profile_lines = [util.shorten_if_long(l) for l in random_profile_lines]
        return random_profile_lines


class Proposal(db.Model):
    from_user = db.ReferenceProperty(reference_class=User, required=True,
                                     collection_name='sent_proposals')
    to_user = db.ReferenceProperty(reference_class=User, required=True,
                                   collection_name='received_proposals')
    created = db.DateTimeProperty(required=True)
    is_active = db.BooleanProperty(required=True)
    is_accepted = db.BooleanProperty(required=True)
