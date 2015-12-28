# -*- coding: utf-8 -*-
from test_bitbucketbase import BitbucketFixture

import json
from uritemplate import expand, variables
from pybitbucket.consumer import Consumer, PermissionScope

import httpretty


class ConsumerFixture(BitbucketFixture):
    # GIVEN: Example data for a consumer resource
    @classmethod
    def resource_data(cls):
        return cls.data_from_file('example_single_consumer.json')

    # GIVEN: Example data for a set of consumer resources
    @classmethod
    def resources_data(cls):
        return cls.data_from_file('example_consumers.json')

    # GIVEN: An example Consumer object created from example data
    @classmethod
    def example_object(cls):
        return Consumer(
            json.loads(cls.resource_data()),
            client=cls.test_client)

    # GIVEN: The URL for the example consumer resource
    @classmethod
    def resource_url(cls):
        o = cls.example_object()
        return o.links['self']['href']

    # GIVEN: The URL for posting consumer resources
    @classmethod
    def resources_url(cls):
        return expand(
            Consumer.get_link_template('consumers'), {
                'bitbucket_url': cls.test_client.get_bitbucket_url(),
                'username': cls.test_client.get_username()})

    # GIVEN: Example inputs for creating a new consumer
    name = 'code-registered-client'
    description = 'Some code added this consumer via the REST API.'
    url = 'http://example.com/'
    callback_url = 'http://localhost'
    scopes = [PermissionScope.REPOSITORY_READ, PermissionScope.EMAIL]
    consumer_id = 302126


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


class TestCreatingPayloadWithInvalidPermissionScope(ConsumerFixture):
    def test_raising_exception_for_not_an_array(self):
        try:
            Consumer.payload(scopes='invalid')
        except Exception as e:
            assert isinstance(e, TypeError)

    def test_raising_exception_for_invalid_permission_scope_name(self):
        try:
            Consumer.payload(scopes=['invalid'])
        except Exception as e:
            assert isinstance(e, NameError)


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
        cls.payload = Consumer.payload(
            name=cls.name,
            scopes=cls.scopes,
            description=cls.description,
            url=cls.url,
            callback_url=cls.callback_url)

    def test_payload_structure_has_2_scopes(self):
        assert 2 == len([
            v
            for (k, v)
            in self.payload
            if k == 'scope'])


class TestCreatingNewConsumer(ConsumerFixture):
    @httpretty.activate
    def test_response_is_a_consumer(self):
        httpretty.register_uri(
            httpretty.POST,
            self.resources_url(),
            content_type='application/json',
            body=self.resource_data(),
            status=200)
        response = Consumer.create(
            name=self.name,
            scopes=self.scopes,
            description=self.description,
            url=self.url,
            callback_url=self.callback_url,
            client=self.test_client)
        assert 'application/x-www-form-urlencoded' == \
            httpretty.last_request().headers.get('Content-Type')
        assert 2 == \
            len(httpretty.last_request().parsed_body.get('scope'))
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
        response = self.example_object().update(
            callback_url=self.new_url)
        assert 'application/x-www-form-urlencoded' == \
            httpretty.last_request().headers.get('Content-Type')
        assert self.new_url == \
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
            self.resources_url(),
            content_type='application/json',
            body=self.resources_data(),
            status=200)
        response = Consumer.find_consumers(client=self.test_client)
        assert isinstance(next(response), Consumer)
