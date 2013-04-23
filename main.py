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
from basehandlers import BaseHandler, LoginRequiredPage


class MeetPage(LoginRequiredPage):
    def get(self):
        state = self.user.state

        if state in [UserState.NO_PERSONAL_INFO, UserState.INACTIVE]:
            self.redirect('/account')

        elif state == UserState.NO_PROFILE:
            self.redirect('/profile')

        elif state == UserState.SHOW_ALL:
            recent_users = User.get_recent_users()
            other_users = filter(lambda u: u.username != self.user.username, recent_users)

            self.render('show_all.html', other_users=other_users, user=self.user)

        elif state == UserState.SHOW_SUMMARY:
            selected_users = list(User.by_profile_uuids(self.user.selected_profile_uuids))

            for user in selected_users:
                user.profile_lines = user.get_random_profile_lines()

            self.render('show_summary.html', selected_users=selected_users, user=self.user)

        elif state == UserState.SHOW_PROFILE:
            selected_users = list(User.by_profile_uuids(self.user.selected_profile_uuids))

            if selected_users:
                self.render('show_profile.html', other_user=selected_users[0], user=self.user)

            else:
                self.write('profile has changed, and is not present anymore')

        else:
            self.error(400)


class ShowSummary(LoginRequiredPage):
    def post(self):
        selected_profile_uuids = self.request.get_all('selected_profile_uuids[]')[:3]
        
        if self.user.state == UserState.SHOW_ALL and selected_profile_uuids:
            self.user.state = UserState.SHOW_SUMMARY
            self.user.selected_profile_uuids = selected_profile_uuids
            self.user.put()
            self.write('success')
        else:
            self.error(400)


class ShowProfile(LoginRequiredPage):
    def post(self):
        selected_profile_uuid = self.request.get('profile_uuid')
        
        if self.user.state == UserState.SHOW_SUMMARY and selected_profile_uuid:
            self.user.state = UserState.SHOW_PROFILE
            self.user.selected_profile_uuids = [selected_profile_uuid]
            self.user.put()
            self.write('success')
        else:
            self.error(400)


class ShowProfile(LoginRequiredPage):
    def post(self):
        selected_profile_uuid = self.request.get('profile_uuid')
        
        if self.user.state == UserState.SHOW_SUMMARY and selected_profile_uuid:
            self.user.state = UserState.SHOW_PROFILE
            self.user.selected_profile_uuids = [selected_profile_uuid]
            self.user.put()
            self.write('success')
        else:
            self.error(400)
            

class TalkPage(LoginRequiredPage):
    def get(self):
        self.render('talk.html', user=self.user)


class ProfilePage(LoginRequiredPage):
    def get(self):
        flashes = self.session.get_flashes()        
        self.render('profile.html', user=self.user, 
                                    flashes=flashes)

    def post(self):
        nickname = self.request.get('nickname')
        tags = self.request.get_all('tag')
        profile = self.request.get('profile')

        if nickname != self.user.nickname or not self.user.profile_uuid:
            self.user.profile_uuid = str(uuid.uuid1())

        self.user.nickname = nickname
        self.user.tags = tags
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


class TestPage(webapp2.RequestHandler):
    def get(self):
        users = User.all()

        for user in users:
            user.state = UserState.SHOW_ALL
            user.put()
                
        self.response.write('success!')

config = {}
config['webapp2_extras.sessions'] = {
    'secret_key': keys.SESSION_SECRET,
}

app = webapp2.WSGIApplication([('/', MainPage),
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