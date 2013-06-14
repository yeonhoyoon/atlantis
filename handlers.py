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
from library.firebase_token_generator import create_token
import logging

class MeetPage(LoginRequiredHandler):
    def get(self):
        state = self.user.state

        if not self.user.verified:
            self.write('Account Not Authorized')

        elif not self.user.has_personal_info():
            self.session.add_flash(u'먼저 기본정보를 작성해 주세요.', level='info')
            self.redirect('/account')

        elif not self.user.has_profile():
            self.session.add_flash(u'먼저 프로필을 작성해 주세요.', level='info')
            self.redirect('/profile')

        elif state == UserState.SHOW_ALL:
            recent_users = User.get_recent_users()
            other_users = filter(lambda u: u.username != self.user.username, recent_users)

            self.render('show_all.html', other_users=other_users)

        elif state == UserState.SHOW_SUMMARY:
            selected_users = list(User.by_profile_uuids(self.user.selected_profile_uuids))

            for user in selected_users:
                user.profile_lines = user.get_random_profile_lines()

            self.render('show_summary.html', selected_users=selected_users)

        elif state == UserState.SHOW_PROFILE:
            other_user = self.user.get_selected_user()

            if other_user:
                self.render('show_profile.html', other_user=other_user)
            else:
                self.write('profile has changed')

        elif state == UserState.PROPOSED:
            other_user_key_id = self.session.get('propose_to_user_key') or \
                             self.user.get_proposed_to_user_key()

            if other_user_key_id:
                self.render('show_profile.html', other_user=User.get_by_id(other_user_key_id), 
                                                 proposed=True)
            else:
                self.write('no proposal exists')

        else:
            self.abort(400)


class ProposalsPage(LoginRequiredHandler):
    def get(self):
        proposed_users = self.user.get_proposed_users()
        for user in proposed_users:
            user.profile_lines = user.get_random_profile_lines()

        self.render('proposals.html', proposed_users=proposed_users)


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


class Propose(LoginRequiredHandler):
    def post(self):
        if self.user.state == UserState.SHOW_PROFILE:
            selected_users = list(User.by_profile_uuids(self.user.selected_profile_uuids))
            other_user = selected_users[0]

            proposal = Proposal(from_user=self.user.key, to_user=other_user.key)
            proposal.put()

            self.user.set_state(UserState.PROPOSED)
            self.user.put()

            self.session['propose_to_user_key'] = other_user.key.id()

        else:
            self.abort(400)


class TalkPage(LoginRequiredHandler):
    def get(self):
        custom_data = {'username': self.user.username}
        options = {}
        #options = { 'debug': True }

        token = create_token(keys.FIREBASE_SECRET, custom_data, options)

        self.render('talk.html', user=self.user, firebase_token=token)


class ProfilePage(LoginRequiredHandler):
    def get(self):
        first_login = self.session.pop('first_login', None)

        self.render('profile.html', user=self.user,
                                    first_login=first_login)

    def post(self):
        nickname = self.request.get('nickname')
        tags = self.request.get_all('tag')
        profile = self.request.get('profile')

        if nickname != self.user.nickname or not self.user.profile_uuid:
            self.user.profile_uuid = str(uuid.uuid1())

        self.user.populate(nickname=nickname, tags=tags, profile=profile)
        self.save_user_and_reload()


class AccountPage(LoginRequiredHandler):
    def get(self):
        self.render('account.html', user=self.user)

    def post(self):
        name = self.request.get('name')
        phone = self.request.get('phone')
        current_password = self.request.get('current_password')
        new_password = self.request.get('new_password')
        verify_new_password = self.request.get('verify_new_password')

        if self.request.get('change_account'):
            self.user.populate(name=name, phone=phone)
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
            self.redirect('/meet')
        else:
            self.render('login.html')


class SignupPage(BaseHandler):
    def get(self):
        if self.logged_in:
            self.redirect('/meet')
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
            user = User.create_user(username=username, raw_password=password)            
            self.auth.set_session(self.auth.store.user_to_dict(user))

            self.session['first_login'] = True
            self.redirect('/profile')

    def get_errors(self, username, password, verify):
        errors = {}

        if not username:
            errors['username'] = u"이메일 주소를 입력해 주세요."

        duplicate_user = User.get_by_id(username)
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

            user = User.get_by_id(username)
            user.verified = True
            user.put()

            self.session.add_flash(u'짝짝짝! 인증이 완료되었습니다.', level='success')

            self.auth.set_session(self.auth.store.user_to_dict(user))
            self.redirect('/meet')
        else:
            self.abort(403)


class LoginPage(BaseHandler):
    def get(self):
        self.render('/login.html', returnurl=self.request.get('returnurl'))

    def post(self):
        username = self.request.get('username')
        password = self.request.get('password')

        try:
            user = self.auth.get_user_by_password(username, password, save_session=True, remember=True)
            self.return_or_redirect('/')

        except (InvalidAuthIdError, InvalidPasswordError) as e:
            self.render('login.html', login_error=True)


class LogoutPage(BaseHandler):
    def get(self):
        self.auth.unset_session()
        self.redirect('/')


class TestPage(webapp2.RequestHandler):
    def get(self):
        for i in range(15):
            user = User.create_user(username='snudatetest' + str(i), raw_password='1234')
            user.name = '김개똥' + str(i)
            user.phone = '01012345678'
            user.nickname = '사용자' + str(i)
            user.tags = [u'예쁘고', u'착하고', u'똑똑한']
            user.profile = """
그대가 돌아서면 두 눈이 마주칠까
심장이 Bounce Bounce 두근대 들릴까 봐 겁나

한참을 망설이다 용기를 내
밤새워 준비한 순애보 고백해도 될까

처음 본 순간부터 네 모습이 
내 가슴 울렁이게 만들었어
Baby You're my trampoline
You make me Bounce Bounce

수많은 인연과 바꾼 너인 걸
사랑이 남긴 상처들도 감싸줄게

어쩌면 우린 벌써 알고 있어
그토록 찾아 헤맨 사랑의 꿈
외롭게만 하는 걸
You make me Bounce You make me Bounce

Bounce Bounce
망설여져 나 혼자만의 감정일까
내가 잘못 생각한 거라면 어떡하지 눈물이나

별처럼 반짝이는 눈망울도
수줍어 달콤하던 네 입술도
내겐 꿈만 같은 걸
You make me Bounce

어쩌면 우린 벌써 알고 있어
그토록 찾아 헤맨 사랑의 꿈
외롭게만 하는 걸 어쩌면 우린 벌써
You make me~ You make me~"""

            user.profile_uuid = str(uuid.uuid1())
            user.verified = True
            user.put()

        self.response.write('success')