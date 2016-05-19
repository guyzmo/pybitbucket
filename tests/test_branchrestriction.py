# -*- coding: utf-8 -*-
from test_bitbucketbase import BitbucketFixture
import json

import httpretty
from uritemplate import expand
from pybitbucket.bitbucket import Bitbucket
from pybitbucket.branchrestriction import (
    BranchRestriction, BranchRestrictionKind, BranchRestrictionPayload)
from pybitbucket.user import User
from voluptuous import MultipleInvalid


class BranchRestrictionFixture(BitbucketFixture):
    # GIVEN: a class under test
    class_under_test = 'BranchRestriction'

    # GIVEN: An example object created from example data
    @classmethod
    def example_object(cls):
        return BranchRestriction(
            json.loads(cls.resource_data()),
            client=cls.test_client)

    # GIVEN: The URL for posting branch-restriction resources
    @classmethod
    def resource_list_url(cls):
        bitbucket = Bitbucket(cls.test_client)
        t = bitbucket.data['_links']['repositoryBranchRestrictions']['href']
        url = expand(
            t, {
                'owner': cls.owner,
                'repository_name': cls.repository_name,
            })
        return url

    # GIVEN: Example data attributes for a build status
    owner = 'ianbuchanan'
    repository_name = 'example'
    restriction_id = 913351
    kind = BranchRestrictionKind.PUSH
    user = 'ian_buchanan'
    users = [user, 'tpettersen']
    group_username = user
    group_name = 'developer-relations'
    pattern = 'feature/*'


class BranchRestrictionPayloadFixture(BranchRestrictionFixture):
    builder = BranchRestrictionPayload()

    # GIVEN: a class under test
    class_under_test = 'BranchRestrictionPayload'

    # GIVEN: An example object created from example data
    @classmethod
    def example_object(cls):
        return BranchRestrictionPayload(json.loads(cls.resource_data()))


class TestGettingTheStringRepresentation(BranchRestrictionFixture):
    @classmethod
    def setup_class(cls):
        cls.branchrestriction_str = str(cls.example_object())

    def test_string_is_not_the_default_format(self):
        assert not self.branchrestriction_str.startswith('<')
        assert not self.branchrestriction_str.endswith('>')

    def test_string_has_the_class_name_and_id_attribute(self):
        assert self.branchrestriction_str.startswith('BranchRestriction id:')


class TestCreatingPushPayloadWithPatternAndUsers(
        BranchRestrictionPayloadFixture):
    @classmethod
    def setup_class(cls):
        cls.payload = BranchRestrictionPayload() \
            .add_kind(BranchRestrictionKind.PUSH) \
            .add_pattern('master') \
            .add_user_by_username('ibuchanan')

    def test_payload_structure(self):
        assert self.payload.validate().build() == {
            "kind": "push",
            "pattern": "master",
            "users": [{
                    "username": "ibuchanan"
                }]
            }


class TestCreatingNewBranchRestriction(BranchRestrictionFixture):
    @classmethod
    def setup_class(cls):
        cls.url = expand(
            BranchRestriction.templates['create'], {
                'bitbucket_url': cls.test_client.get_bitbucket_url(),
                'owner': cls.owner,
                'repository_name': cls.repository_name
            })

    @httpretty.activate
    def test_response_is_a_branchrestriction(self):
        print(self.url)
        httpretty.register_uri(
            httpretty.POST,
            self.url,
            content_type='application/json',
            body=self.resource_data(),
            status=200)
        payload = BranchRestrictionPayload() \
            .add_kind(self.kind) \
            .add_pattern(self.pattern) \
            .add_user_by_username(self.user) \
            .add_owner(self.owner) \
            .add_repository_name(self.repository_name)
        response = BranchRestriction.create(payload, client=self.test_client)
        assert 'application/json' == \
            httpretty.last_request().headers.get('Content-Type')
        assert isinstance(response, BranchRestriction)


class TestUpdatingBranchRestriction(BranchRestrictionFixture):
    @httpretty.activate
    def test_response_is_a_branchrestriction(self):
        httpretty.register_uri(
            httpretty.PUT,
            self.resource_url(),
            content_type='application/json',
            body=self.resource_data(),
            status=200)
        payload = BranchRestrictionPayload() \
            .add_kind(BranchRestrictionKind.PUSH) \
            .add_pattern('developing')
        response = self.example_object().modify(payload)
        assert 'application/json' == \
            httpretty.last_request().headers.get('Content-Type')
        assert isinstance(response, BranchRestriction)


class TestFindingBranchRestrictions(BranchRestrictionFixture):
    @httpretty.activate
    def test_response_is_a_branchrestriction_generator(self):
        httpretty.register_uri(
            httpretty.GET,
            self.resource_list_url(),
            content_type='application/json',
            body=self.resource_list_data(),
            status=200)
        response = BranchRestriction.find_branchrestrictions_for_repository(
            owner=self.owner,
            repository_name=self.repository_name)
        assert isinstance(next(response), BranchRestriction)


class TestFindingBranchRestrictionById(BranchRestrictionFixture):
    @httpretty.activate
    def test_response_is_a_branchrestriction(self):
        httpretty.register_uri(
            httpretty.GET,
            self.resource_url(),
            content_type='application/json',
            body=self.resource_data(),
            status=200)
        response = \
            BranchRestriction.find_branchrestriction_for_repository_by_id(
                owner=self.owner,
                repository_name=self.repository_name,
                restriction_id=self.restriction_id)
        assert isinstance(response, BranchRestriction)


class TestDeletingBranchRestriction(BranchRestrictionFixture):
    @httpretty.activate
    def test_response_is_not_an_exception(self):
        httpretty.register_uri(
            httpretty.DELETE,
            self.resource_url(),
            status=204)
        result = self.example_object().delete()
        assert result is None


class TestCreatingDefaultBranchRestrictionPayload(
        BranchRestrictionPayloadFixture):
    @classmethod
    def setup_class(cls):
        cls.data = cls.builder.build()

    def test_default_payload_is_empty_dictionary(self):
        assert {} == self.data

    def test_default_is_invalid(self):
        try:
            self.builder.validate()
            assert False
        except Exception as e:
            assert isinstance(e, MultipleInvalid)


class TestAddingOwnerToBranchRestrictionPayload(
        BranchRestrictionPayloadFixture):
    @classmethod
    def setup_class(cls):
        cls.with_owner = cls.builder.add_owner(cls.owner)

    def test_immutability_after_add(self):
        assert self.with_owner
        assert {} == self.builder.build()

    def test_structure(self):
        assert self.owner == self.with_owner.owner


class TestAddingUsersToBranchRestrictionPayload(
        BranchRestrictionPayloadFixture):
    @classmethod
    def setup_class(cls):
        cls.with_user = \
            cls.builder.add_user_by_username(
                cls.user)
        cls.with_users = \
            cls.builder.add_users_from_usernames(
                cls.users)
        cls.user_obj = User(
            json.loads(cls.resource_data('User')),
            client=cls.test_client)
        cls.with_user_obj = cls.builder.add_user(cls.user_obj)

    def test_immutability_on_adding_users(self):
        assert self.with_user
        assert self.with_users
        assert {} == self.builder.build()

    def test_users_structure_for_one(self):
        expected = {
            'users': [
                {'username': self.user}
            ]
        }
        assert expected == self.with_user.build()

    def test_users_structure_for_many(self):
        expected = {'users': [{'username': u} for u in self.users]}
        assert expected == self.with_users.build()

    def test_users_structure_for_user_obj(self):
        expected = {
            'users': [
                {'username': 'evzijst'}
            ]
        }
        assert expected == self.with_user_obj.build()


class TestCreatingMinimalBranchRestrictionPayload(
        BranchRestrictionPayloadFixture):
    @classmethod
    def setup_class(cls):
        cls.payload = BranchRestrictionPayload() \
            .add_kind(cls.kind) \
            .add_pattern(cls.pattern)
        cls.expected = json.loads(cls.resource_data(
            'BranchRestrictionPayload.minimal'))

    def test_minimum_viable_payload_structure_for_create(self):
        assert self.payload.validate().build() == self.expected


class TestCreatingFullBranchRestrictionPayload(
        BranchRestrictionPayloadFixture):
    @classmethod
    def setup_class(cls):
        cls.payload = BranchRestrictionPayload() \
            .add_kind(BranchRestrictionKind.DELETE) \
            .add_pattern(cls.pattern) \
            .add_user_by_username(cls.user) \
            .add_group_by_username_and_groupname(
                cls.group_username,
                cls.group_name)
        cls.expected = json.loads(cls.resource_data(
            'BranchRestrictionPayload.full'))

    def test_full_payload_structure(self):
        assert self.payload.validate().build() == self.expected
