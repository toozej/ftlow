#!/usr/bin/env python2
# -*- coding: utf-8 -*-

"""
    ftlow Tests
    ~~~~~~~~~~~~

    Tests the ftlow application. These tests are based heavily off
    the Flaskr tests written by Armin Ronacher located at
    github.com/mitsuhiko/flask/blob/master/examples/flaskr/flaskr_tests.py

    :copyright: (c) 2013 by James Tooze.
    :license: BSD, see LICENSE for more details.
"""
import os
import ftlow
import unittest
import tempfile


class ftlowTestCase(unittest.TestCase):

    def setUp(self):
        """Before each test, set up a blank database"""
        self.db_fd, ftlow.app.config['DATABASE'] = tempfile.mkstemp()
        ftlow.app.config['TESTING'] = True
        self.app = ftlow.app.test_client()
        ftlow.init_db()

    def tearDown(self):
        """Get rid of the database again after each test."""
        os.close(self.db_fd)
        os.unlink(ftlow.app.config['DATABASE'])

    def login(self, username, password):
        return self.app.post('/login', data=dict(
            username=username,
            password=password
        ), follow_redirects=True)

    def logout(self):
        return self.app.get('/logout', follow_redirects=True)

    # testing functions

    def test_empty_db(self):
        """Start with a blank database."""
        rv = self.app.get('/')
        assert 'No entries here so far' in rv.data

    def test_login_logout(self):
        """Make sure login and logout works"""
        rv = self.login(ftlow.app.config['USERNAME'],
                        ftlow.app.config['PASSWORD'])
        assert 'You were logged in' in rv.data
        rv = self.logout()
        assert 'You were logged out' in rv.data
        rv = self.login(ftlow.app.config['USERNAME'] + 'x',
                        ftlow.app.config['PASSWORD'])
        assert 'Invalid username' in rv.data
        rv = self.login(ftlow.app.config['USERNAME'],
                        ftlow.app.config['PASSWORD'] + 'x')
        assert 'Invalid password' in rv.data

    def test_messages(self):
        """Test that messages work"""
        self.login(ftlow.app.config['USERNAME'],
                   ftlow.app.config['PASSWORD'])
        rv = self.app.post('/add', data=dict(
            title='<Hello>',
            text='<strong>HTML</strong> allowed here'
        ), follow_redirects=True)
        assert 'No entries here so far' not in rv.data
        assert '&lt;Hello&gt;' in rv.data
        assert '<strong>HTML</strong> allowed here' in rv.data


if __name__ == '__main__':
    unittest.main()
