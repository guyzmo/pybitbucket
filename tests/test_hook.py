# -*- coding: utf-8 -*-
from test_bitbucketbase import BitbucketFixture
import json

import httpretty
from uritemplate import expand
from pybitbucket.hook import (Hook, HookPayload, HookEvent)
from pybitbucket.bitbucket import Bitbucket
from pybitbucket.repository import Repository


class HookFixture(BitbucketFixture):
    # GIVEN: a class under test
    class_under_test = 'Hook'

    # GIVEN: An example object created from example data
    @classmethod
    def example_object(cls):
        return Hook(
            json.loads(cls.resource_data()),
            client=cls.test_client)

    # GIVEN: Example data attributes for a hook
    owner = 'pybitbucket'
    repository_name = 'testing'
    hook_uuid = '{ec96bf6b-abb2-4f30-90b9-0178342c9fc5}'
    callback_url = 'https://example.com/bitbucket/'
    description = 'WebHook Description'
    active = True
    skip_cert_verification = False
    events = [HookEvent.REPOSITORY_PUSH]


class HookPayloadFixture(HookFixture):
    builder = HookPayload()

    # GIVEN: a class under test
    class_under_test = 'HookPayload'

    # GIVEN: An example object created from example data
    @classmethod
    def example_object(cls):
        return HookPayload(json.loads(cls.resource_data()))


class TestGettingTheStringRepresentation(HookFixture):
    @classmethod
    def setup_class(cls):
        cls.hook_str = str(cls.example_object())

    def test_string_is_not_the_default_format(self):
        assert not self.hook_str.startswith('<')
        assert not self.hook_str.endswith('>')

    def test_string_has_the_class_name_and_id_attribute(self):
        assert self.hook_str.startswith('Hook uuid:')


class TestCheckingTheExampleData(HookFixture):
    @classmethod
    def setup_class(cls):
        cls.data = json.loads(cls.resource_data())

    def test_passes_the_type_check(self):
        assert Hook.is_type(self.data)


class TestAccessingHookAttributes(HookFixture):
    @classmethod
    def setup_class(cls):
        cls.response = cls.example_object()

    def test_common_attributes_are_valid(self):
        assert self.hook_uuid == self.response.uuid
        assert self.callback_url == self.response.url
        assert self.description == self.response.description
        assert self.active == self.response.active
        assert self.skip_cert_verification == \
            self.response.skip_cert_verification

    def test_date_attributes(self):
        assert self.response.created_at

    def test_subject_is_a_repository(self):
        assert isinstance(self.response.subject, Repository)

    def test_events_are_valid(self):
        assert self.events == self.response.events


class TestCreatingNewHook(HookFixture):
    @classmethod
    def setup_class(cls):
        cls.url = expand(
            Hook.templates['create'], {
                'bitbucket_url': cls.test_client.get_bitbucket_url(),
                'owner': cls.test_client.get_username(),
                'repository_name': cls.repository_name,
            })

    @httpretty.activate
    def test_response_is_a_hook(self):
        httpretty.register_uri(
            httpretty.POST,
            self.url,
            content_type='application/json',
            body=self.resource_data(),
            status=200)
        payload = HookPayload() \
            .add_description(self.description) \
            .add_callback_url(self.callback_url) \
            .add_events(self.events) \
            .activate() \
            .enable_cert_verification()
        response = Hook.create(
            payload=payload,
            repository_name=self.repository_name,
            owner=self.owner,
            client=self.test_client)
        assert 'application/json' == \
            httpretty.last_request().headers.get('Content-Type')
        assert isinstance(response, Hook)


class TestUpdating(HookFixture):
    new_url = 'http://www.example.com'

    @httpretty.activate
    def test_response_is_a_hook(self):
        httpretty.register_uri(
            httpretty.PUT,
            self.resource_url(),
            content_type='application/json',
            body=self.resource_data(),
            status=200)
        payload = HookPayload() \
            .add_description(self.description) \
            .add_callback_url(self.new_url)
        response = self.example_object().update(payload=payload)
        assert self.new_url == \
            httpretty.last_request().parsed_body['url']
        assert isinstance(response, Hook)


class TestDeleting(HookFixture):
    @httpretty.activate
    def test_response_is_not_an_exception(self):
        httpretty.register_uri(
            httpretty.DELETE,
            self.resource_url(),
            status=204)
        result = self.example_object().delete()
        assert result is None


class TestFindingHookByUuid(HookFixture):
    @httpretty.activate
    def test_response_is_a_hook(self):
        httpretty.register_uri(
            httpretty.GET,
            self.resource_url(),
            content_type='application/json',
            body=self.resource_data(),
            status=200)
        response = Hook.find_hook_by_uuid_in_repository(
            uuid=self.hook_uuid,
            repository_name=self.repository_name,
            owner=self.owner,
            client=self.test_client)
        assert isinstance(response, Hook)


class TestFindingHooksForRepository(HookFixture):
    @classmethod
    def setup_class(cls):
        template = (
            Bitbucket(client=cls.test_client)
            .data
            .get('_links', {})
            .get('repositoryHooks', {})
            .get('href'))
        cls.url = expand(
            template, {
                'bitbucket_url': cls.test_client.get_bitbucket_url(),
                'owner': cls.owner,
                'repository_name': cls.repository_name
            })

    @httpretty.activate
    def test_response_is_a_hook_generator(self):
        httpretty.register_uri(
            httpretty.GET,
            self.url,
            content_type='application/json',
            body=self.resource_list_data(),
            status=200)
        response = Hook.find_hooks_for_repository(
            repository_name=self.repository_name,
            client=self.test_client)
        assert isinstance(next(response), Hook)


class TestCreatingMinimalHookPayload(HookPayloadFixture):
    @classmethod
    def setup_class(cls):
        cls.payload = HookPayload() \
            .add_description(cls.description) \
            .add_callback_url(cls.callback_url)
        cls.expected = json.loads(cls.resource_data(
            'HookPayload.minimal'))

    def test_minimum_viable_payload_structure_for_create(self):
        assert self.payload.validate().build() == self.expected


class TestCreatingFullPullHookPayload(HookPayloadFixture):
    @classmethod
    def setup_class(cls):
        cls.payload = HookPayload() \
            .add_description(cls.description) \
            .add_callback_url(cls.callback_url) \
            .add_events(cls.events) \
            .activate() \
            .enable_cert_verification()
        cls.expected = json.loads(cls.resource_data(
            'HookPayload.full'))

    def test_full_payload_structure(self):
        assert self.payload.validate().build() == self.expected
