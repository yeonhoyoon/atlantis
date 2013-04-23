# -*- coding: utf-8 -*-
import os
import re
from datetime import datetime, timedelta
import uuid
import webapp2
import jinja2
from webapp2_extras import sessions
from model import User, Proposal, UserState
import util
import keys

jinja_env = jinja2.Environment(autoescape = True,
                               loader = jinja2.FileSystemLoader(
                               os.path.join(os.path.dirname(__file__), 'templates')))


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
