# -*- coding: utf-8 -*-
import os
import re
from datetime import datetime, timedelta
import uuid
import webapp2
import jinja2
from webapp2_extras import sessions
from webapp2_extras import auth
from model import User, Proposal, UserState, UserToken
import keys
from util import util, xsrf
import logging
import main


jinja_env = jinja2.Environment(autoescape = True,
                               loader = jinja2.FileSystemLoader(
                               os.path.join(os.path.dirname(__file__), 'templates')))


class BaseHandler(webapp2.RequestHandler):
    def write(self, *a, **kw):
        self.response.write(*a, **kw)

    def render_str(self, template, **params):
        t = jinja_env.get_template(template)
        
        if self.logged_in:
            params['user_info'] = self.user_info
            params['xsrf_token'] = self.xsrf_token

        return t.render(params)

    def render(self, template, **kw):
        self.write(self.render_str(template, **kw))

    @webapp2.cached_property
    def auth(self):
        return auth.get_auth()

    @webapp2.cached_property
    def user_info(self):
        return self.auth.get_user_by_session()

    @webapp2.cached_property
    def user(self):
        u = self.user_info
        us = self.user_model.get_by_id(u['username']) if u else None
        return us

    @webapp2.cached_property
    def logged_in(self):
        return self.user_info is not None

    @webapp2.cached_property
    def user_model(self):
        return self.auth.store.user_model

    @webapp2.cached_property
    def session(self):
        return self.session_store.get_session()

    @webapp2.cached_property
    def xsrf_token(self):
        token = util.read_secure_cookie(self.request, '_xsrf_token')
        if not token:
            token = xsrf.XSRFToken(user_id=self.user_info['username'], 
                                   secret=keys.XSRF_SECRET).generate_token_string()
            util.set_secure_cookie(self.response, '_xsrf_token', token)
        return token

    def check_xsrf_token(self):
        if self.request.method == 'POST' and self.logged_in:
            received_token = (self.request.get('_xsrf_token') or 
                              self.request.headers.get('X-XSRF-Token'))

            if not self.xsrf_token or self.xsrf_token != received_token:
                self.abort(403)
    
    def dispatch(self):
        self.session_store = sessions.get_store(request=self.request)        

        self.check_xsrf_token()
        
        try:        
            webapp2.RequestHandler.dispatch(self)
        finally:
            self.session_store.save_sessions(self.response)
   

    def current_uri(self):
        return self.uri_for(self.__class__.__name__)

    def save_user_and_reload(self):
        self.user.put()
        self.session.add_flash(u'변경 사항을 저장하였습니다.', level='success')
        self.redirect(self.current_uri())


class LoginRequiredHandler(BaseHandler):
    def initialize(self, *a, **kw):
        BaseHandler.initialize(self, *a, **kw)

        if not self.logged_in:
            self.redirect('/login?returnurl=' + self.current_uri(), abort=True)
        elif (self.user_info['state'] == UserState.NOT_AUTH and 
           self.request.path not in ['/account', '/profile', '/send_verification_email']):
           self.redirect('/account', abort=True)