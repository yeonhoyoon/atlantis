# -*- coding: utf-8 -*-
import os
import re
from datetime import datetime, timedelta
import base64
import uuid
import webapp2
import jinja2
from google.appengine.api import mail
from webapp2_extras import sessions, auth
from webapp2_extras.auth import InvalidAuthIdError, InvalidPasswordError
from model import User, Proposal, UserState, UserToken
from util import util
import keys
from basehandlers import BaseHandler, LoginRequiredHandler
import logging

class MeetPage(LoginRequiredHandler):
    def get(self):
        state = self.user.state

        if state == UserState.NOT_AUTH:
            self.write('Account Not Authorized')

        elif state in [UserState.NO_PERSONAL_INFO, UserState.INACTIVE]:
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
            self.abort(400)


class ShowSummary(LoginRequiredHandler):
    def post(self):
        selected_profile_uuids = self.request.get_all('selected_profile_uuids[]')[:3]
        
        if self.user.state == UserState.SHOW_ALL and selected_profile_uuids:
            self.user.state = UserState.SHOW_SUMMARY
            self.user.selected_profile_uuids = selected_profile_uuids
            self.user.put()
            self.write('success')
        else:
            self.abort(400)


class ShowProfile(LoginRequiredHandler):
    def post(self):
        selected_profile_uuid = self.request.get('profile_uuid')
        
        if self.user.state == UserState.SHOW_SUMMARY and selected_profile_uuid:
            self.user.state = UserState.SHOW_PROFILE
            self.user.selected_profile_uuids = [selected_profile_uuid]
            self.user.put()
            self.write('success')
        else:
            self.abort(400)


class ShowProfile(LoginRequiredHandler):
    def post(self):
        selected_profile_uuid = self.request.get('profile_uuid')
        
        if self.user.state == UserState.SHOW_SUMMARY and selected_profile_uuid:
            self.user.state = UserState.SHOW_PROFILE
            self.user.selected_profile_uuids = [selected_profile_uuid]
            self.user.put()
            self.write('success')
        else:
            self.abort(400)


class Propose(LoginRequiredHandler):
    pass


class TalkPage(LoginRequiredHandler):
    def get(self):
        self.render('talk.html', user=self.user)


class ProfilePage(LoginRequiredHandler):
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

        self.save_user_and_reload()


class AccountPage(LoginRequiredHandler):
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
            self.save_user_and_reload()

        elif self.request.get('change_password'):
            password_errors = {}
            try:
                User.get_by_auth_password(self.user.username, current_password)
            except InvalidPasswordError as e:
                password_errors['current_password'] = u'현재 비밀번호가 맞지 않습니다.'
            if new_password != verify_new_password:
                password_errors['verify_password'] = u'비밀번호와 비밀번호 확인이 다릅니다.'

            if not password_errors:
                self.user.set_password(new_password)
                self.save_user_and_reload()
            else:
                self.render('account.html', user=self.user, password_errors=password_errors)


class MainPage(BaseHandler):
    def get(self):
        if self.logged_in:
            first_login = self.session.pop('first_login', None)
            self.render('main.html', first_login=first_login)
        else:
           self.render('signup.html')


class CreateAccount(BaseHandler):
    def post(self):
        username = self.request.get('username')
        password = self.request.get('password')
        verify = self.request.get('verify')
        errors = self.get_errors(username, password, verify)

        if errors:
            self.render('signup.html', errors=errors)
        else:
            user = User.create_user(username=username, raw_password=password)            
            self.auth.set_session(self.auth.store.user_to_dict(user))

            self.session['first_login'] = True
            self.redirect('/')

    def get_errors(self, username, password, verify):
        errors = {}

        if not username:
            errors['username'] = u"이메일 주소를 입력해 주세요."

        duplicate_user = User.get_by_username(username)
        if duplicate_user:
            errors['username_error'] = u"이미 등록된 사용자입니다."

        if not password:
            errors['password_error'] = u'비밀번호를 입력해 주세요.'

        if password != verify:
            errors['verify_error'] = u"비밀번호와 비밀번호 확인이 다릅니다."
        
        return errors


class SendVerificationEmail(LoginRequiredHandler):
    def post(self):
        username = self.user_info['username']
        token = User.create_signup_token(username)


        user_address = username + '@snu.ac.kr'
        sender_address = '스누데이트 <support@snudate.com>'
        subject = u'[스누데이트] 가입을 환영합니다!'
        link = 'http://snudate.com/verify/{0}-{1}'.format(base64.b64encode(username), token)
        body = """
안녕하세요!
스누데이트에 오신것을 환영합니다.
스누데이트를 통해 좋은 인연을 만날 수 있기를 바랍니다. :)

다음 링크를 클릭하여 서울대학교 구성원임을 인증해 주세요.

{0}

감사합니다.
""".format(link)

        mail.send_mail(sender_address, user_address, subject, body)

class Verify(BaseHandler):
    def get(self, encoded_username, signup_token):
        username = base64.b64decode(encoded_username)
        if User.validate_signup_token(username, signup_token):
            User.delete_signup_token(username, signup_token)

            user = User.get_by_username(username)
            user.state = UserState.SHOW_ALL
            user.update_state()

            self.auth.set_session(self.auth.store.user_to_dict(user))
            self.redirect('/meet')
        else:
            self.abort(403)


class LoginPage(BaseHandler):
    def get(self):
        self.render('/login.html')

    def post(self):
        username = self.request.get('username')
        password = self.request.get('password')

        try:
            user = self.auth.get_user_by_password(username, password, save_session=True)
            returnurl = self.request.get('returnurl')
            if returnurl:
                self.redirect(str(returnurl))
            else:
                self.redirect('/')
        except (InvalidAuthIdError, InvalidPasswordError) as e:
            self.render('login.html', login_error=True)


class LogoutPage(BaseHandler):
    def get(self):
        self.auth.unset_session()
        self.redirect('/')


class TestPage(webapp2.RequestHandler):
    def get(self):
        token = util.generate_xsrf_token()
        self.response.write(token)