# -*- coding: utf-8 -*-
from test_bitbucketbase import BitbucketFixture

import json
from uritemplate import expand
from pybitbucket.user import User, UserV1
from pybitbucket.bitbucket import Bitbucket

import httpretty


class UserFixture(BitbucketFixture):
    # GIVEN: a class under test
    class_under_test = 'User'

    # GIVEN: An example object created from example data
    @classmethod
    def example_object(cls):
        return User(
            json.loads(cls.resource_data()),
            client=cls.test_client)

    # GIVEN: Example data attributes a user
    username = 'evzijst'


class UserV1Fixture(BitbucketFixture):
    # GIVEN: a class under test
    class_under_test = 'UserV1'

    # GIVEN: An example object created from example data
    @classmethod
    def example_object(cls):
        return UserV1(
            json.loads(cls.resource_data()),
            client=cls.test_client)

    # GIVEN: Example data attributes a user
    username = 'ianbuchanan'


class TestGettingTheStringRepresentation(UserFixture):
    @classmethod
    def setup_class(cls):
        cls.user_str = str(cls.example_object())

    def test_string_is_not_the_default_format(self):
        assert not self.user_str.startswith('<')
        assert not self.user_str.endswith('>')

    def test_string_has_the_class_name_and_id_attribute(self):
        assert self.user_str.startswith('User username:')


class TestCheckingTheExampleData(UserFixture):
    @classmethod
    def setup_class(cls):
        cls.data = json.loads(cls.resource_data())

    def test_passes_the_type_check(self):
        assert User.is_type(self.data)


class TestCheckingTheExampleDataForV1(UserV1Fixture):
    @classmethod
    def setup_class(cls):
        cls.data = json.loads(cls.resource_data())

    def test_passes_the_type_check(self):
        assert UserV1.is_type(self.data)


class TestFindingUserByUsername(UserFixture):
    @httpretty.activate
    def test_response_is_a_user(self):
        httpretty.register_uri(
            httpretty.GET,
            self.resource_url(),
            content_type='application/json',
            body=self.resource_data(),
            status=200)
        response = User.find_user_by_username(
            username=self.username,
            client=self.test_client)
        assert isinstance(response, User)
        assert 'evzijst' == response.username
        assert 'Erik van Zijst' == response.display_name


class TestFindingCurrentUser(UserFixture):
    @httpretty.activate
    def test_response_is_a_user(self):
        url = (
            Bitbucket(client=self.test_client)
            .data
            .get('_links', {})
            .get('userForMyself', {})
            .get('href'))
        httpretty.register_uri(
            httpretty.GET,
            url,
            content_type='application/json',
            body=self.resource_data(),
            status=200)
        response = User.find_current_user(client=self.test_client)
        assert isinstance(response, User)
        assert 'evzijst' == response.username
        assert 'Erik van Zijst' == response.display_name


class TestCallingFollowersLink(UserFixture):
    @httpretty.activate
    def test_response_is_a_list_of_users(self):
        user = self.example_object()
        url = user.links.get('followers', {}).get('href')
        httpretty.register_uri(
            httpretty.GET,
            url,
            content_type='application/json',
            body=self.resource_list_data(),
            status=200)
        assert list(user.followers())
        assert isinstance(next(user.followers()), User)


class TestCommonAttributesForV1andV2(UserV1Fixture):
    @httpretty.activate
    def test_attributes_are_not_empty(self):
        user = self.example_object()
        assert user.username
        assert user.display_name


class TestNavigatingToOAuthConsumers(UserFixture):
    @httpretty.activate
    def test_attributes_are_not_empty(self):
        from pybitbucket.consumer import Consumer
        user = self.example_object()
        url = user.v1.links.get('consumers', {}).get('href')
        example = self.data_from_file('Consumer_list.json')
        httpretty.register_uri(
            httpretty.GET,
            url,
            content_type='application/json',
            body=example,
            status=200)
        assert list(user.v1.consumers())
        assert isinstance(next(user.v1.consumers()), Consumer)


class TestNavigatingFromV1toV2(UserV1Fixture):
    @classmethod
    def setup_class(cls):
        cls.response = cls.example_object()
        user_template = (
            Bitbucket(client=cls.test_client)
            .data
            .get('_links', {})
            .get('userByUsername', {})
            .get('href'))
        cls.user_url = expand(
            user_template, {
                'bitbucket_url': cls.test_client.get_bitbucket_url(),
                'username': cls.username,
            })
        cls.user_data = cls.resource_list_data('User')

    @httpretty.activate
    def test_v2_self_returns_a_user(self):
        httpretty.register_uri(
            httpretty.GET,
            self.user_url,
            content_type='application/json',
            body=self.user_data,
            status=200)
        response = self.response.v2.self()
        assert isinstance(response, User)
