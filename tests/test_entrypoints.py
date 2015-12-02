# -*- coding: utf-8 -*-
import httpretty
from os import path
from test_auth import TestAuth

from pybitbucket.bitbucket import Bitbucket
from pybitbucket.bitbucket import Client


class TestEntrypoints(object):
    @classmethod
    def setup_class(cls):
        cls.test_dir, current_file = path.split(path.abspath(__file__))
        cls.client = Client(TestAuth())

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
        user = next(Bitbucket(client=self.client).userForMyself())
        assert 'evzijst' == user.username
        assert 'Erik van Zijst' == user.display_name

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
        user = next(Bitbucket(client=self.client).userByUsername(
            username='evzijst'))
        assert 'evzijst' == user.username
        assert 'Erik van Zijst' == user.display_name
