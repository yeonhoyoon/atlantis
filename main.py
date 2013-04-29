# -*- coding: utf-8 -*-
import os
import re
from datetime import datetime, timedelta
import uuid
import webapp2
import jinja2
from webapp2_extras import sessions
from model import User, Proposal, UserState
from handlers import (MainPage, MeetPage, ShowSummary, ShowProfile, 
                      Propose, TalkPage, ProfilePage, AccountPage, 
                      TestPage, LoginPage, LogoutPage, CreateAccount, 
                      SendVerificationEmail, Verify)
import keys
from util import util, xsrf
import logging
from basehandlers import jinja_env

config = {
  'webapp2_extras.sessions': {
    'secret_key': keys.SESSION_SECRET,
    'cookie_args': { 'httponly': True }
  },
  'webapp2_extras.auth': {
    'user_model': 'model.User',
    'user_attributes': ['username', 'state']
  }
}

app = webapp2.WSGIApplication([('/', MainPage),
   webapp2.Route('/create_account', CreateAccount, name='CreateAccount'),
   webapp2.Route('/send_verification_email', SendVerificationEmail, 
                 name='SendVerificationEmail'),
   webapp2.Route('/verify/<encoded_username:.+>-<signup_token:.+>', Verify, name='Verify'),
   webapp2.Route('/meet', MeetPage, name='MeetPage'),
   webapp2.Route('/meet/show_summary', ShowSummary, name='ShowSummary'),
   webapp2.Route('/meet/show_profile', ShowProfile, name='ShowProfile'),
   webapp2.Route('/meet/propose', Propose, name='Propose'),
   webapp2.Route('/talk', TalkPage, name='TalkPage'),
   webapp2.Route('/profile', ProfilePage, name='ProfilePage'),
   webapp2.Route('/account', AccountPage, name='AccountPage'),
   ('/test123', TestPage),
   ('/login', LoginPage),
   ('/logout', LogoutPage)],
   config = config,
   debug=True)

