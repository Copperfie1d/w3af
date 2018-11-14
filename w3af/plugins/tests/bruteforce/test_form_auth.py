"""
test_form_auth.py

Copyright 2012 Andres Riancho

This file is part of w3af, http://w3af.org/ .

w3af is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation version 2 of the License.

w3af is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with w3af; if not, write to the Free Software
Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
"""
import os

from nose.plugins.attrib import attr

from w3af import ROOT_PATH
from w3af.plugins.tests.helper import PluginTest, PluginConfig, MockResponse
from w3af.core.controllers.ci.moth import get_moth_http


class GenericFormAuthTest(PluginTest):
    BASE_PATH = os.path.join(ROOT_PATH, 'plugins', 'tests', 'bruteforce')

    small_users_negative = os.path.join(BASE_PATH, 'small-users-negative.txt')
    small_users_positive = os.path.join(BASE_PATH, 'small-users-positive.txt')
    small_passwords = os.path.join(BASE_PATH, 'small-passwords.txt')

    basic_config = {
        'crawl': (PluginConfig('web_spider',
                               ('only_forward', True, PluginConfig.BOOL),),),
        'bruteforce': (PluginConfig('form_auth',
                                    ('usersFile',
                                     small_users_positive,
                                     PluginConfig.STR),

                                    ('passwdFile',
                                     small_passwords,
                                     PluginConfig.INPUT_FILE),

                                    ('useProfiling',
                                     False,
                                     PluginConfig.BOOL),),),
    }


class FormAuthTest(GenericFormAuthTest):
    
    BASE_PATH = os.path.join(ROOT_PATH, 'plugins', 'tests', 'bruteforce')
    
    target_post_url = get_moth_http('/bruteforce/form/guessable_login_form.py')
    target_get_url = get_moth_http('/bruteforce/form/guessable_login_form_get.py')
    target_password_only_url = get_moth_http('/bruteforce/form/guessable_pass_only.py')
    target_negative_url = get_moth_http('/bruteforce/form/impossible.py')

    target_web_spider_url = get_moth_http('/bruteforce/form/')

    negative_test = {
        'crawl': (PluginConfig('web_spider',
                              ('only_forward', True, PluginConfig.BOOL),),),
        'bruteforce': (PluginConfig('form_auth',

                                    ('usersFile',
                                     GenericFormAuthTest.small_users_negative,
                                     PluginConfig.STR),

                                    ('passwdFile',
                                     GenericFormAuthTest.small_passwords,
                                     PluginConfig.INPUT_FILE),

                                    ('useProfiling',
                                     False,
                                     PluginConfig.BOOL),),)
    }

    @attr('smoke')
    def test_found_credentials_post(self):
        self._scan(self.target_post_url, self.basic_config)

        # Assert the general results
        vulns = self.kb.get('form_auth', 'auth')
        self.assertEquals(len(vulns), 1)

        vuln = vulns[0]

        self.assertEquals(vuln.get_name(), 'Guessable credentials')
        self.assertEquals(vuln.get_url().url_string, self.target_post_url)
        self.assertEquals(vuln['user'], 'admin')
        self.assertEquals(vuln['pass'], '1234')

    def test_found_credentials_get(self):
        self._scan(self.target_get_url, self.basic_config)

        # Assert the general results
        vulns = self.kb.get('form_auth', 'auth')
        self.assertEquals(len(vulns), 1)

        vuln = vulns[0]

        self.assertEquals(vuln.get_name(), 'Guessable credentials')
        self.assertEquals(vuln.get_url().url_string, self.target_get_url)
        self.assertEquals(vuln['user'], 'admin')
        self.assertEquals(vuln['pass'], 'admin')

    def test_found_credentials_password_only(self):
        self._scan(self.target_password_only_url, self.basic_config)

        # Assert the general results
        vulns = self.kb.get('form_auth', 'auth')
        self.assertEquals(len(vulns), 1, vulns)

        vuln = vulns[0]

        self.assertEquals(vuln.get_name(), 'Guessable credentials')
        self.assertEquals(vuln.get_url().url_string,
                          self.target_password_only_url)
        self.assertEquals(vuln['user'], 'password-only-form')
        self.assertEquals(vuln['pass'], '1234')

    def test_negative(self):
        self._scan(self.target_negative_url, self.negative_test)

        # Assert the general results
        vulns = self.kb.get('form_auth', 'auth')
        self.assertEquals(len(vulns), 0)


class TestFormAuthFailedLoginMatch(GenericFormAuthTest):

    target_url = u'http://w3af.org/'
    login_url = u'http://w3af.org/login'

    FORM = ('<form method="POST" action="/login">'
            '    <input name="username" type="text" />'
            '    <input name="password" type="password" />'
            '    <input name="submit" type="submit" />'
            '</form>')

    def request_callback(self, request, uri, response_headers):
        response_headers['content-type'] = 'text/html'

        username = request.parsed_body.get('username', [''])[0]
        password = request.parsed_body.get('password', [''])[0]

        if username == 'admin' and password == 'admin':
            body = 'Welcome Mr. Admin'
        else:
            body = 'Fail'

        return 200, response_headers, body

    MOCK_RESPONSES = [
              MockResponse(url=target_url,
                           body=FORM,
                           status=200,
                           method='GET',
                           content_type='text/html'),

              MockResponse(url=login_url,
                           body=request_callback,
                           method='POST',
                           content_type='text/html',
                           status=200),

    ]

    def test_found_credentials_post(self):
        self._scan(self.target_url, self.basic_config)

        # Assert the general results
        vulns = self.kb.get('form_auth', 'auth')
        self.assertEquals(len(vulns), 1)

        vuln = vulns[0]

        self.assertEquals(vuln.get_name(), 'Guessable credentials')
        self.assertEquals(vuln.get_url().url_string, self.login_url)
        self.assertEquals(vuln['user'], 'admin')
        self.assertEquals(vuln['pass'], 'admin')
