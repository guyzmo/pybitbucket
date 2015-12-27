# -*- coding: utf-8 -*-
from test_bitbucketbase import BitbucketFixture

import json
from uritemplate import expand
from pybitbucket.bitbucket import Bitbucket
from pybitbucket.branchrestriction import (
    BranchRestriction, BranchRestrictionKind)

import httpretty


class BranchRestrictionFixture(BitbucketFixture):
    # GIVEN: An example repository owner and name
    owner = 'ianbuchanan'
    repository_name = 'example'

    # GIVEN: An ID for an example branch-restriction resource
    restriction_id = 913351

    # GIVEN: Example data for a branch-restriction resource
    @classmethod
    def resource_data(cls):
        return cls.data_from_file('example_single_branchrestriction.json')

    # GIVEN: Example data for a set of branch-restriction resources
    @classmethod
    def resources_data(cls):
        return cls.data_from_file('example_branchrestrictions.json')

    # GIVEN: An example BranchRestriction object created from example data
    @classmethod
    def example_object(cls):
        return BranchRestriction(
            json.loads(cls.resource_data()),
            client=cls.test_client)

    # GIVEN: The URL for the example branch-restriction resource
    @classmethod
    def resource_url(cls):
        o = cls.example_object()
        return o.links['self']['href']

    # GIVEN: The URL for posting branch-restriction resources
    @classmethod
    def resources_url(cls):
        bitbucket = Bitbucket(cls.test_client)
        t = bitbucket.data['_links']['repositoryBranchRestrictions']['href']
        url = expand(
            t, {
                'owner': cls.owner,
                'repository_name': cls.repository_name,
            })
        return url


class TestGettingTheStringRepresentation(BranchRestrictionFixture):
    @classmethod
    def setup_class(cls):
        cls.branchrestriction_str = str(cls.example_object())

    def test_string_is_not_the_default_format(self):
        assert not self.branchrestriction_str.startswith('<')
        assert not self.branchrestriction_str.endswith('>')

    def test_string_has_the_class_name_and_id_attribute(self):
        assert self.branchrestriction_str.startswith('BranchRestriction id:')


class TestCreatingPayloadWithInvalidRestrictionKind(BranchRestrictionFixture):
    def test_raising_exception_for_invalid_restriction_kind(self):
        try:
            BranchRestriction.payload(kind='invalid')
        except Exception as e:
            assert isinstance(e, NameError)


class TestCreatingPushPayloadWithPatternAndUsers(BranchRestrictionFixture):
    @classmethod
    def setup_class(cls):
        cls.payload = BranchRestriction.payload(
            kind=BranchRestrictionKind.PUSH,
            pattern='master',
            users=['ibuchanan'])

    def test_payload_structure(self):
        assert self.payload == {
            "kind": "push",
            "pattern": "master",
            "users": [{
                    "username": "ibuchanan"
                }]
            }


class TestCreatingNewBranchRestriction(BranchRestrictionFixture):
    @httpretty.activate
    def test_response_is_a_branchrestriction(self):
        httpretty.register_uri(
            httpretty.POST,
            self.resources_url(),
            content_type='application/json',
            body=self.resource_data(),
            status=200)
        response = BranchRestriction.create(
            owner=self.owner,
            repository_name=self.repository_name,
            kind=BranchRestrictionKind.PUSH,
            pattern='master',
            users=['ibuchanan'])
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
        response = self.example_object().update(
            pattern='developing')
        assert 'application/json' == \
            httpretty.last_request().headers.get('Content-Type')
        assert isinstance(response, BranchRestriction)


class TestFindingBranchRestrictions(BranchRestrictionFixture):
    @httpretty.activate
    def test_response_is_a_branchrestriction_generator(self):
        httpretty.register_uri(
            httpretty.GET,
            self.resources_url(),
            content_type='application/json',
            body=self.resources_data(),
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
