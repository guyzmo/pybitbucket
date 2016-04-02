# -*- coding: utf-8 -*-
from test_bitbucketbase import BitbucketFixture
import json

import httpretty
from uritemplate import expand
from pybitbucket.build import (
    BuildStatus, BuildStatusStates, BuildStatusPayload)
from voluptuous import MultipleInvalid


class BuildStatusFixture(BitbucketFixture):
    # GIVEN: a class under test
    class_under_test = 'BuildStatus'

    # GIVEN: An example object created from example data
    @classmethod
    def example_object(cls):
        return BuildStatus(
            json.loads(cls.resource_data()),
            client=cls.test_client)

    # GIVEN: Example data attributes for a build status
    owner = 'emmap1'
    repository_name = 'MyRepo'
    revision = '61d9e64348f9da407e62f64726337fd3bb24b466'
    key = 'BAMBOO-PROJECT-X'
    state = BuildStatusStates.SUCCESSFUL
    url = 'https://example.com/path/to/build'
    name = 'Build #34'
    description = 'Changes by John Doe'


class BuildStatusPayloadFixture(BuildStatusFixture):
    builder = BuildStatusPayload()

    # GIVEN: a class under test
    class_under_test = 'BuildStatusPayload'

    # GIVEN: An example object created from example data
    @classmethod
    def example_object(cls):
        return BuildStatusPayload(json.loads(cls.resource_data()))


class TestGettingTheStringRepresentation(BuildStatusFixture):
    @classmethod
    def setup_class(cls):
        cls.buildstatus_str = str(cls.example_object())

    def test_string_is_not_the_default_format(self):
        assert not self.buildstatus_str.startswith('<')
        assert not self.buildstatus_str.endswith('>')

    def test_string_has_the_class_name_and_id_attribute(self):
        assert self.buildstatus_str.startswith('BuildStatus key:')


class TestCheckingTheExampleData(BuildStatusFixture):
    @classmethod
    def setup_class(cls):
        cls.data = json.loads(cls.resource_data())

    def test_passes_the_type_check(self):
        assert BuildStatus.is_type(self.data)


class TestAccessingBuildStatusAttributes(BuildStatusFixture):
    @classmethod
    def setup_class(cls):
        cls.response = cls.example_object()

    def test_common_attributes_are_valid(self):
        assert self.state == self.response.state
        assert self.key == self.response.key
        assert self.name == self.response.name
        assert self.url == self.response.url
        assert self.description == self.response.description


class TestDeleting(BuildStatusFixture):
    @httpretty.activate
    def test_response_is_not_an_exception(self):
        httpretty.register_uri(
            httpretty.DELETE,
            self.resource_url(),
            status=204)
        result = self.example_object().delete()
        assert result is None


class TestCreatingNewBuildStatus(BuildStatusFixture):
    @classmethod
    def setup_class(cls):
        cls.url = expand(
            BuildStatus.templates['create'], {
                'bitbucket_url': cls.test_client.get_bitbucket_url(),
                'owner': cls.test_client.get_username(),
                'repository_name': cls.repository_name,
                'revision': cls.revision
            })

    @httpretty.activate
    def test_response_is_a_buildstatus(self):
        httpretty.register_uri(
            httpretty.POST,
            self.url,
            content_type='application/json',
            body=self.resource_data(),
            status=200)
        payload = BuildStatusPayload() \
            .add_key(self.key) \
            .add_state(self.state) \
            .add_url(self.url) \
            .add_name(self.name) \
            .add_description(self.description) \
            .add_repository_name(self.repository_name) \
            .add_revision(self.revision)
        response = BuildStatus.create(payload, client=self.test_client)
        assert 'application/json' == \
            httpretty.last_request().headers.get('Content-Type')
        assert isinstance(response, BuildStatus)


class TestModifyingBuildStatus(BuildStatusFixture):
    @classmethod
    def setup_class(cls):
        cls.url = cls.example_object().links['self']['href']

    @httpretty.activate
    def test_response_is_a_buildstatus(self):
        httpretty.register_uri(
            httpretty.PUT,
            self.url,
            content_type='application/json',
            body=self.resource_data(),
            status=200)
        payload = BuildStatusPayload() \
            .add_key(self.key) \
            .add_state(self.state) \
            .add_url(self.url) \
            .add_name(self.name) \
            .add_description(self.description)
        response = self.example_object().modify(payload)
        assert 'application/json' == \
            httpretty.last_request().headers.get('Content-Type')
        assert isinstance(response, BuildStatus)


class TestCreatingDefaultBuildStatusPayload(BuildStatusPayloadFixture):
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


class TestAddingKeyToBuildStatusPayload(BuildStatusPayloadFixture):
    @classmethod
    def setup_class(cls):
        cls.with_key = cls.builder.add_key(cls.key)

    def test_immutability_after_add(self):
        assert self.with_key
        assert {} == self.builder.build()

    def test_structure(self):
        expected = {
            'key': self.key
        }
        assert expected == self.with_key.build()


class TestAddingStateToBuildStatusPayload(BuildStatusPayloadFixture):
    @classmethod
    def setup_class(cls):
        cls.with_state = cls.builder.add_state(cls.state)

    def test_immutability_after_add(self):
        assert self.with_state
        assert {} == self.builder.build()

    def test_structure(self):
        expected = {
            'state': self.state
        }
        assert expected == self.with_state.build()


class TestAddingUrlToBuildStatusPayload(BuildStatusPayloadFixture):
    @classmethod
    def setup_class(cls):
        cls.with_url = cls.builder.add_url(cls.url)

    def test_immutability_after_add(self):
        assert self.with_url
        assert {} == self.builder.build()

    def test_structure(self):
        expected = {
            'url': self.url
        }
        assert expected == self.with_url.build()


class TestAddingNameToBuildStatusPayload(BuildStatusPayloadFixture):
    @classmethod
    def setup_class(cls):
        cls.with_name = cls.builder.add_name(cls.name)

    def test_immutability_after_add(self):
        assert self.with_name
        assert {} == self.builder.build()

    def test_structure(self):
        expected = {
            'name': self.name
        }
        assert expected == self.with_name.build()


class TestAddingDescriptionToBuildStatusPayload(BuildStatusPayloadFixture):
    @classmethod
    def setup_class(cls):
        cls.with_description = cls.builder.add_description(cls.description)

    def test_immutability_after_add(self):
        assert self.with_description
        assert {} == self.builder.build()

    def test_structure(self):
        expected = {
            'description': self.description
        }
        assert expected == self.with_description.build()


class TestAddingOwnerToBuildStatusPayload(BuildStatusPayloadFixture):
    @classmethod
    def setup_class(cls):
        cls.with_owner = cls.builder.add_owner(cls.owner)

    def test_immutability_after_add(self):
        assert self.with_owner
        assert {} == self.builder.build()

    def test_structure(self):
        assert self.owner == self.with_owner.owner


class TestAddingRevisionToBuildStatusPayload(BuildStatusPayloadFixture):
    @classmethod
    def setup_class(cls):
        cls.with_revision = cls.builder.add_revision(cls.revision)

    def test_immutability_after_add(self):
        assert self.with_revision
        assert {} == self.builder.build()

    def test_structure(self):
        assert self.revision == self.with_revision.revision


class TestAddingRepositoryNameToBuildStatusPayload(BuildStatusPayloadFixture):
    @classmethod
    def setup_class(cls):
        cls.with_repository_name = cls.builder.add_repository_name(
            cls.repository_name)

    def test_immutability_after_add(self):
        assert self.with_repository_name
        assert {} == self.builder.build()

    def test_structure(self):
        assert self.repository_name == \
            self.with_repository_name.repository_name


class TestCreatingMinimalBuildStatusPayload(BuildStatusPayloadFixture):
    @classmethod
    def setup_class(cls):
        cls.payload = BuildStatusPayload() \
            .add_key(cls.key) \
            .add_state(cls.state) \
            .add_url(cls.url)
        cls.expected = json.loads(cls.resource_data(
            'BuildStatusPayload.minimal'))

    def test_minimum_viable_payload_structure_for_create(self):
        assert self.payload.validate().build() == self.expected


class TestCreatingFullBuildStatusPayload(BuildStatusPayloadFixture):
    @classmethod
    def setup_class(cls):
        cls.payload = BuildStatusPayload() \
            .add_key(cls.key) \
            .add_state(cls.state) \
            .add_url(cls.url) \
            .add_name(cls.name) \
            .add_description(cls.description)
        cls.expected = json.loads(cls.resource_data(
            'BuildStatusPayload.full'))

    def test_minimum_viable_payload_structure_for_create(self):
        assert self.payload.validate().build() == self.expected


class TestFindingBuildStatusForRepositoryCommitByKey(BuildStatusFixture):
    @httpretty.activate
    def test_response_is_a_buildstatus(self):
        httpretty.register_uri(
            httpretty.GET,
            self.resource_url(),
            content_type='application/json',
            body=self.resource_data(),
            status=200)
        response = BuildStatus.find_buildstatus_for_repository_commit_by_key(
            repository_name=self.repository_name,
            revision=self.revision,
            key=self.key,
            owner=self.owner,
            client=self.test_client)
        assert isinstance(response, BuildStatus)
