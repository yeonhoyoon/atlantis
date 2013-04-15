import os
import re
import webapp2
import jinja2
from google.appengine.ext import db
import util


PASSWORD_RE = re.compile(r"^.{4,100}$")

jinja_env = jinja2.Environment(autoescape = True,
                               loader = jinja2.FileSystemLoader(
                                os.path.join(os.path.dirname(__file__), 'templates')))


class User(db.Model):
    email = db.EmailProperty(required=True)
    password = db.StringProperty(required=True)
    last_active = db.DateTimeProperty(required=True, auto_now_add=True)
    created = db.DateTimeProperty(required=True, auto_now_add=True)
    email_confirmed = db.BooleanProperty(required=True, default=False)

    name = db.StringProperty()
    phone = db.PhoneNumberProperty()
    gender = db.CategoryProperty(choices=set(['M', 'F']))
    contact_allowed_gender = db.CategoryProperty(choices=set(['M', 'F', 'MF']))
    birth_year = db.IntegerProperty()
    region = db.CategoryProperty()
    tags = db.StringProperty()
    profile = db.TextProperty()
    
    remaining_choices = db.IntegerProperty(required=True, default=3)
    remaining_proposals = db.IntegerProperty(required=True, default=1)
    remaining_accepts = db.IntegerProperty(required=True, default=1)
    is_matched = db.BooleanProperty(required=True, default=False)
    last_match = db.DateTimeProperty()
    is_active = db.BooleanProperty(required=True, default=True)

    @classmethod
    def by_email(cls, email):
        user = cls.all().filter('email =', email).get()
        return user


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


class MainPage(BaseHandler):
    def get(self):
        self.render('main.html', title='main page')


class DatesPage(BaseHandler):
    def get(self):
        users = User.all().run()
        self.render('dates.html', users=users)


class SignupPage(BaseHandler):
    def get(self):
        self.render('signup.html')

    def post(self):
        email = self.request.get('email')
        password = self.request.get('password')
        verify = self.request.get('verify')

        errors = self.get_errors(email, password, verify)

        if errors:
            self.render('signup.html', **dict({ 'email': email }.items() +
                                              errors.items()))
        else:
            hashed = util.make_password_hash(password)
            user = User(email=email, password=hashed)
            user.put()

            self.login(user)
            self.redirect('/dates')

    def get_errors(self, email, password, verify):
        errors = {}

        duplicate_user = User.by_email(email)
        if duplicate_user:
            errors['email_error'] = "Duplicate user exists."

        if PASSWORD_RE.match(password) is None:
            errors['password_error'] = "That's not a valid password."
        if password != verify:
            errors['verify_error'] = "Passwords don't match."
        
        return errors


app = webapp2.WSGIApplication([('/', MainPage),
                               ('/dates', DatesPage),
                               ('/signup', SignupPage)],
                               debug=True)