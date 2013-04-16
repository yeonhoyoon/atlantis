# -*- coding: utf-8 -*-
import os
import re
import webapp2
import jinja2
from google.appengine.ext import db
from webapp2_extras import sessions
import util
import keys

jinja_env = jinja2.Environment(autoescape = True,
                               loader = jinja2.FileSystemLoader(
                               os.path.join(os.path.dirname(__file__), 'templates')))


class User(db.Model):
    username = db.StringProperty(required=True)
    password = db.StringProperty(required=True)
    last_active = db.DateTimeProperty(required=True, auto_now_add=True)
    created = db.DateTimeProperty(required=True, auto_now_add=True)
    confirmed = db.BooleanProperty(required=True, default=False)

    name = db.StringProperty()
    phone = db.PhoneNumberProperty()
    gender = db.CategoryProperty(choices=set(['M', 'F']))
    contact_allowed_gender = db.CategoryProperty(choices=set(['M', 'F', 'MF']))
    birth_year = db.IntegerProperty()
    region = db.CategoryProperty()
    nickname = db.StringProperty()
    tags = db.StringProperty()
    profile = db.TextProperty()
    
    remaining_choices = db.IntegerProperty(required=True, default=3)
    remaining_proposals = db.IntegerProperty(required=True, default=1)
    remaining_accepts = db.IntegerProperty(required=True, default=1)
    is_matched = db.BooleanProperty(required=True, default=False)
    last_match = db.DateTimeProperty()
    is_active = db.BooleanProperty(required=True, default=True)

    @classmethod
    def by_username(cls, username):
        user = cls.all().filter('username =', username).get()
        return user

    @classmethod
    def validate(cls, name, password):
        user = cls.by_username(name)
        if user and util.check_password(password, user.password):
            return user

    def get_tags(self):
        if self.tags:
            return self.tags.split('|')
        else: 
            return ['', '', '']

    def set_tags(self, tags):
        if tags:
            self.tags = '|'.join(map(lambda tag: tag.replace('|', ''), tags))


class Proposal(db.Model):
    from_user = db.ReferenceProperty(reference_class=User, required=True,
                                     collection_name='sent_proposals')
    to_user = db.ReferenceProperty(reference_class=User, required=True,
                                   collection_name='received_proposals')
    created = db.DateTimeProperty(required=True)
    is_active = db.BooleanProperty(required=True)
    is_accepted = db.BooleanProperty(required=True)


class BaseHandler(webapp2.RequestHandler):
    def write(self, *a, **kw):
        self.response.write(*a, **kw)

    def render_str(self, template, **params):
        t = jinja_env.get_template(template)
        return t.render(params)

    def render(self, template, **kw):
        self.write(self.render_str(template, **kw))

    def set_secure_cookie(self, name, value):
        cookie_value = util.make_cookie_value(value)
        self.response.headers.add_header(
            'Set-Cookie', 
            '{0}={1}; Path=/'.format(name, cookie_value))

    def read_secure_cookie(self, name):
        cookie_value = self.request.cookies.get(name)
        return cookie_value and util.check_cookie_value(cookie_value)

    def login(self, user):
        self.set_secure_cookie('user_id', str(user.key().id()))

    def logout(self):
        self.response.headers.add_header('Set-Cookie', 'user_id=; Path=/')

    def initialize(self, *a, **kw):
        webapp2.RequestHandler.initialize(self, *a, **kw)
        uid = self.read_secure_cookie('user_id')
        self.user = uid and User.get_by_id(int(uid))

    def dispatch(self):
        self.session_store = sessions.get_store(request=self.request)        
        try:
            webapp2.RequestHandler.dispatch(self)
        finally:
            self.session_store.save_sessions(self.response)

    @webapp2.cached_property
    def session(self):
        return self.session_store.get_session()

    def current_uri(self):
        return self.uri_for(self.__class__.__name__)

    def save_user_and_redirect(self):
        self.user.put()
        self.session.add_flash(u'변경 사항을 저장하였습니다.', level='success')
        self.redirect(self.current_uri())


class LoginRequiredPage(BaseHandler):
    def initialize(self, *a, **kw):
        BaseHandler.initialize(self, *a, **kw)
        if not self.user:
            self.redirect('/login?returnurl=' + self.current_uri())


class MeetPage(LoginRequiredPage):
    def get(self):
        users = User.all().run()
        self.render('meet.html', users=users, user=self.user)


class TalkPage(LoginRequiredPage):
    def get(self):
        self.render('talk.html', user=self.user)


class ProfilePage(LoginRequiredPage):
    def get(self):
        flashes = self.session.get_flashes()        
        self.render('profile.html', user=self.user, 
                                    tags=self.user.get_tags(), 
                                    flashes=flashes)

    def post(self):
        nickname = self.request.get('nickname')
        tag0 = self.request.get('tag0')
        tag1 = self.request.get('tag1')
        tag2 = self.request.get('tag2')
        profile = self.request.get('profile')

        self.user.nickname = nickname
        self.user.set_tags([tag0, tag1, tag2])
        self.user.profile = profile

        self.save_user_and_redirect()


class AccountPage(LoginRequiredPage):
    def get(self):
        flashes = self.session.get_flashes()
        self.render('account.html', user=self.user, flashes=flashes)

    def post(self):
        name = self.request.get('name')
        phone = self.request.get('phone')
        current_password = self.request.get('current_password')
        new_password = self.request.get('new_password')
        verify_new_password = self.request.get('verify_new_password')

        if self.request.get('change_account'):
            self.user.name = name
            self.user.phone = phone
            self.save_user_and_redirect()

        elif self.request.get('change_password'):
            password_errors = {}
            if not util.check_password(current_password, self.user.password):
                password_errors['current_password'] = u'현재 비밀번호가 맞지 않습니다.'
            if new_password != verify_new_password:
                password_errors['verify_password'] = u'비밀번호와 비밀번호 확인이 다릅니다.'

            if not password_errors:
                self.user.password = util.make_password_hash(new_password)
                self.save_user_and_redirect()
            else:
                self.render('account.html', user=self.user, password_errors=password_errors)


class MainPage(BaseHandler):
    def get(self):
        if self.user:
            self.render('main.html', user=self.user)
        else:
            self.render('signup.html')

    def post(self):
        username = self.request.get('username')
        password = self.request.get('password')
        verify = self.request.get('verify')
        errors = self.get_errors(username, password, verify)

        if errors:
            self.render('signup.html', errors=errors)
        else:
            hashed = util.make_password_hash(password)
            user = User(username=username, password=hashed)
            user.put()

            self.login(user)
            self.redirect('/')

    def get_errors(self, username, password, verify):
        errors = {}

        duplicate_user = User.by_username(username)
        if duplicate_user:
            errors['username_error'] = u"이미 등록된 사용자입니다."

        if not password:
            errors['password_error'] = u'비밀번호를 입력해 주세요.'

        if password != verify:
            errors['verify_error'] = u"비밀번호와 비밀번호 확인이 다릅니다."
        
        return errors


class LoginPage(BaseHandler):
    def get(self):
        self.render('/login.html')

    def post(self):
        username = self.request.get('username')
        password = self.request.get('password')

        user = User.validate(username, password)
        if user:
            self.login(user)

            returnurl = self.request.get('returnurl')
            if returnurl:
                self.redirect(str(returnurl))
            else:
                self.redirect('/')
        else:
            self.render('login.html', login_error=True)


class LogoutPage(BaseHandler):
    def get(self):
        self.logout()
        self.redirect('/')

config = {}
config['webapp2_extras.sessions'] = {
    'secret_key': keys.SESSION_SECRET,
}

app = webapp2.WSGIApplication([('/', MainPage),
                               webapp2.Route('/meet', MeetPage, name='MeetPage'),
                               webapp2.Route('/talk', TalkPage, name='TalkPage'),
                               webapp2.Route('/profile', ProfilePage, name='ProfilePage'),
                               webapp2.Route('/account', AccountPage, name='AccountPage'),
                               ('/login', LoginPage),
                               ('/logout', LogoutPage)],
                               config = config,
                               debug=True)