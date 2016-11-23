# -*- coding: utf-8 -*-
from test_bitbucketbase import BitbucketFixture
import json

import httpretty
from uritemplate import expand, variables
from pybitbucket.consumer import Consumer, ConsumerPayload, PermissionScope
from voluptuous import MultipleInvalid


class ConsumerFixture(BitbucketFixture):
    # GIVEN: a class under test
    class_under_test = 'Consumer'

    # GIVEN: An example object created from example data
    @classmethod
    def example_object(cls):
        return Consumer(
            json.loads(cls.resource_data()),
            client=cls.test_client)

    # GIVEN: The URL for the example resource
    @classmethod
    def resource_url(cls):
        return expand(
            Consumer(client=cls.test_client).templates['self'], {
                'bitbucket_url': cls.test_client.get_bitbucket_url(),
                'username': cls.test_client.get_username(),
                'consumer_id': cls.consumer_id
            })

    # GIVEN: The URL for listing example resources
    @classmethod
    def resource_list_url(cls):
        return expand(
            Consumer(client=cls.test_client).templates['self'], {
                'bitbucket_url': cls.test_client.get_bitbucket_url(),
                'username': cls.test_client.get_username(),
            })

    # GIVEN: Example inputs for creating a new consumer
    name = 'code-registered-client'
    description = 'Some code added this consumer via the REST API.'
    consumer_url = 'http://example.com/'
    callback_url = 'http://localhost'
    scopes = [PermissionScope.REPOSITORY_READ, PermissionScope.EMAIL]
    consumer_id = 302126
    consumer_key = '6qErCQRtk2nmVHuemM'
    shared_secret = '96ztLLDzvrT5zmchsdZZLKCkTMkUkb4W'


class ConsumerPayloadFixture(ConsumerFixture):
    builder = ConsumerPayload()

    # GIVEN: a class under test
    class_under_test = 'ConsumerPayload'

    # GIVEN: An example object created from example data
    @classmethod
    def example_object(cls):
        return ConsumerPayload(json.loads(cls.resource_data()))


class TestGettingTheStringRepresentation(ConsumerFixture):
    @classmethod
    def setup_class(cls):
        cls.branchrestriction_str = str(cls.example_object())

    def test_string_is_not_the_default_format(self):
        assert not self.branchrestriction_str.startswith('<')
        assert not self.branchrestriction_str.endswith('>')

    def test_string_has_the_class_name_and_id_attribute(self):
        assert self.branchrestriction_str.startswith('Consumer id:')


class TestCheckingTheExampleData(ConsumerFixture):
    @classmethod
    def setup_class(cls):
        cls.data = json.loads(cls.resource_data())

    def test_passes_the_type_check_for_consumer(self):
        assert Consumer.is_type(self.data)


class TestGettingLinks(ConsumerFixture):
    @classmethod
    def setup_class(cls):
        cls._self = Consumer.get_link_template('self')
        cls._owner = Consumer.get_link_template('owner')
        cls._consumers = Consumer.get_link_template('consumers')

    def test_self_has_an_id(self):
        assert 'consumer_id' in variables(self._self)

    def test_owner_is_identified_by_username(self):
        assert 'username' in variables(self._owner)

    def test_consumers_only_needs_bitbucket_url_and_username(self):
        assert set(['username', 'bitbucket_url']) == \
            variables(self._consumers)


class TestCreatingConsumerPayload(ConsumerPayloadFixture):
    @classmethod
    def setup_class(cls):
        cls.payload = ConsumerPayload() \
            .add_name(cls.name)

    def test_payload_structure(self):
        assert self.payload.validate().build() == {
                "name": self.name,
            }


class TestCreatingPayloadWithInvalidPermissionScope(ConsumerFixture):
    @classmethod
    def setup_class(cls):
        cls.builder = ConsumerPayload() \
            .add_name(cls.name)

    def test_raising_exception_for_not_an_array(self):
        try:
            self.builder = self.builder.add_scopes('invalid')
            self.builder = self.builder.validate()
            assert False
        except Exception as e:
            assert isinstance(e, MultipleInvalid)

    def test_raising_exception_for_invalid_permission_scope_name(self):
        try:
            self.builder = self.builder.add_scope('invalid')
            self.builder = self.builder.validate()
            assert False
        except Exception as e:
            assert isinstance(e, MultipleInvalid)


class TestDeletingConsumer(ConsumerFixture):
    @httpretty.activate
    def test_response_is_not_an_exception(self):
        httpretty.register_uri(
            httpretty.DELETE,
            self.resource_url(),
            status=204)
        result = self.example_object().delete()
        assert result is None


class TestCreatingPayload(ConsumerFixture):
    @classmethod
    def setup_class(cls):
        cls.payload = ConsumerPayload() \
            .add_name(cls.name) \
            .add_description(cls.description) \
            .add_url(cls.consumer_url) \
            .add_callback_url(cls.callback_url) \
            .add_scopes(cls.scopes) \
            .validate() \
            .build()

    def test_payload_structure_has_2_scopes(self):
        assert 2 == len(self.payload.get('scopes'))


class TestCreatingNewConsumer(ConsumerFixture):
    @classmethod
    def setup_class(cls):
        cls.url = expand(
            Consumer(client=cls.test_client).templates['create'], {
                'bitbucket_url': cls.test_client.get_bitbucket_url(),
                'username': cls.test_client.get_username(),
            })

    @httpretty.activate
    def test_response_is_a_consumer(self):
        httpretty.register_uri(
            httpretty.POST,
            self.url,
            content_type='application/json',
            body=self.resource_data(),
            status=200)
        payload = ConsumerPayload() \
            .add_name(self.name) \
            .add_description(self.description) \
            .add_url(self.consumer_url) \
            .add_callback_url(self.callback_url) \
            .add_scopes(self.scopes)
        response = Consumer.create(payload, client=self.test_client)
        assert 'application/x-www-form-urlencoded' == \
            httpretty.last_request().headers.get('Content-Type')
        assert 2 == \
            len(httpretty.last_request().parsed_body.get('scopes'))
        assert isinstance(response, Consumer)


class TestGettingExpandedSelfUrl(ConsumerFixture):
    def test_url_has_id(self):
        assert (
            'https://staging.bitbucket.org/api' +
            '/1.0/users/' +
            'pybitbucket' +
            '/consumers/' +
            str(self.consumer_id)) == \
            self.example_object().links['self']['href']


class TestUpdatingConsumer(ConsumerFixture):
    new_url = 'http://www.example.com'

    @httpretty.activate
    def test_response_is_a_consumer(self):
        httpretty.register_uri(
            httpretty.PUT,
            self.resource_url(),
            content_type='application/json',
            body=self.resource_data(),
            status=200)
        payload = ConsumerPayload() \
            .add_name(self.name) \
            .add_callback_url(self.callback_url)
        response = self.example_object().update(payload=payload)
        assert 'application/x-www-form-urlencoded' == \
            httpretty.last_request().headers.get('Content-Type')
        assert self.callback_url == \
            httpretty.last_request().parsed_body['callback_url'][0]
        assert isinstance(response, Consumer)


class TestFindingConsumerById(ConsumerFixture):
    @httpretty.activate
    def test_response_is_a_consumer(self):
        httpretty.register_uri(
            httpretty.GET,
            self.resource_url(),
            content_type='application/json',
            body=self.resource_data(),
            status=200)
        response = \
            Consumer.find_consumer_by_id(
                consumer_id=self.consumer_id,
                client=self.test_client)
        assert isinstance(response, Consumer)


class TestFindingConsumers(ConsumerFixture):
    @httpretty.activate
    def test_response_is_a_consumer_generator(self):
        httpretty.register_uri(
            httpretty.GET,
            self.resource_list_url(),
            content_type='application/json',
            body=self.resource_list_data(),
            status=200)
        response = Consumer.find_consumers(client=self.test_client)
        assert isinstance(next(response), Consumer)


class TestCreatingDefaultConsumerPayload(ConsumerPayloadFixture):
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


class TestCreatingMinimalConsumerPayload(ConsumerPayloadFixture):
    @classmethod
    def setup_class(cls):
        cls.payload = ConsumerPayload() \
            .add_name(cls.name)
        cls.expected = json.loads(cls.resource_data(
            'ConsumerPayload.minimal'))

    def test_minimum_viable_payload_structure_for_create(self):
        assert self.payload.validate().build() == self.expected


class TestCreatingFullConsumerPayload(ConsumerPayloadFixture):
    @classmethod
    def setup_class(cls):
        cls.payload = ConsumerPayload() \
            .add_name(cls.name) \
            .add_description(cls.description) \
            .add_url(cls.consumer_url) \
            .add_key(cls.consumer_key) \
            .add_secret(cls.shared_secret) \
            .add_callback_url(cls.callback_url) \
            .add_consumer_id(cls.consumer_id)
        cls.expected = json.loads(cls.resource_data(
            'ConsumerPayload.full'))

    def test_full_payload_structure(self):
        assert self.payload.validate().build() == self.expected
