# -*- coding: utf-8 -*-
import httpretty
import json
from os import path
from test_auth import TestAuth

from pybitbucket.user import User
from pybitbucket.bitbucket import Client


class TestUser(object):
    @classmethod
    def setup_class(cls):
        cls.test_dir, current_file = path.split(path.abspath(__file__))
        cls.client = Client(TestAuth())

    def test_user_string_representation(self):
        example_path = path.join(self.test_dir, 'example_single_user.json')
        with open(example_path) as f:
            example = json.load(f)
        user = User(example, client=self.client)
        # Just tests that the __str__ method works and
        # that it does not use the default representation
        user_str = "%s" % user
        print(user_str)
        assert not user_str.startswith('<')
        assert not user_str.endswith('>')
        assert user_str.startswith('User username:')

    @httpretty.activate
    def test_find_user_by_username(self):
        url = ('https://api.bitbucket.org/2.0/users/evzijst')
        example_path = path.join(self.test_dir, 'example_single_user.json')
        with open(example_path) as f:
            example = f.read()
        httpretty.register_uri(
            httpretty.GET,
            url,
            content_type='application/json',
            body=example,
            status=200)
        user = User.find_user_by_username('evzijst', client=self.client)
        assert 'evzijst' == user.username
        assert 'Erik van Zijst' == user.display_name

    @httpretty.activate
    def test_followers_link(self):
        url = ('https://api.bitbucket.org/2.0/users/evzijst')
        example_path = path.join(self.test_dir, 'example_single_user.json')
        with open(example_path) as f:
            example = f.read()
        httpretty.register_uri(
            httpretty.GET,
            url,
            content_type='application/json',
            body=example,
            status=200)
        user = User.find_user_by_username('evzijst', client=self.client)

        url = ('https://' +
               'api.bitbucket.org' +
               '/2.0/users/evzijst/followers')
        example_path = path.join(self.test_dir, 'example_followers.json')
        with open(example_path) as f:
            example = f.read()
        httpretty.register_uri(
            httpretty.GET,
            url,
            content_type='application/json',
            body=example,
            status=200)
        my_follower = next(user.followers())
        assert 'mg' == my_follower.username
        assert 'Martin Geisler' == my_follower.display_name

    @httpretty.activate
    def test_find_current_user(self):
        url = ('https://api.bitbucket.org/2.0/user')
        example_path = path.join(self.test_dir, 'example_single_user.json')
        with open(example_path) as f:
            example = f.read()
        httpretty.register_uri(
            httpretty.GET,
            url,
            content_type='application/json',
            body=example,
            status=200)
        user = User.find_current_user(client=self.client)
        assert 'evzijst' == user.username
        assert 'Erik van Zijst' == user.display_name
