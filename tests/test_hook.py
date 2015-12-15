# -*- coding: utf-8 -*-
import httpretty
from os import path
from test_auth import TestAuth

from util import data_from_file

from pybitbucket.hook import Hook
from pybitbucket.bitbucket import Client


class TestSnippet(object):
    hook_uuid = 'ec96bf6b-abb2-4f30-90b9-0178342c9fc5'

    @classmethod
    def setup_class(cls):
        cls.test_dir, current_file = path.split(path.abspath(__file__))
        cls.client = Client(TestAuth())

    @httpretty.activate
    def test_create_webhook(self):
        url = (
            self.client.get_bitbucket_url() +
            '/2.0/repositories/pybitbucket/testing/hooks')
        example = data_from_file(
            self.test_dir,
            'example_webhook.json')
        httpretty.register_uri(
            httpretty.POST,
            url,
            content_type='application/json',
            body=example,
            status=200)
        new_hook = Hook.create_hook(
            'testing',
            'WebHook Description',
            'https://example.com/bitbucket/',
            active=True,
            events=['repo:push'],
            client=self.client,
        )
        assert new_hook.description == 'WebHook Description'
        assert new_hook.url == 'https://example.com/bitbucket/'
        assert new_hook.events == ['repo:push']
        assert new_hook.active

    def test_create_webhook_payload(self):
        payload = Hook.make_payload(
            'WebHook Description',
            'https://example.com/bitbucket',
            active=True,
            events=['repo:push'],
        )

        assert payload['description'] == 'WebHook Description'
        assert payload['url'] == 'https://example.com/bitbucket'
        assert payload['active']
        assert payload['events'] == ['repo:push']

    def test_create_webhook_payload_use_defaults(self):
        payload = Hook.make_payload(
            'WebHook Description',
            'https://example.com/bitbucket',
        )

        assert 'https://example.com/bitbucket' == payload.get('url')
        assert payload.get('active')
        assert 'WebHook Description' == payload.get('description')
        assert 'repo:push' == payload.get('events')[0]

    @httpretty.activate
    def test_modify_webhook(self):
        url = (
            self.client.get_bitbucket_url() +
            '/2.0/repositories/pybitbucket/testing/hooks/' +
            self.hook_uuid)
        example = data_from_file(
            self.test_dir,
            'example_modified_webhook.json')
        httpretty.register_uri(
            httpretty.PUT,
            url,
            content_type='application/json',
            body=example,
            status=200)
        hook = Hook({
            "uuid": "{ec96bf6b-abb2-4f30-90b9-0178342c9fc5}",
            "links": {
                "self": {"href": url}
            },
            "url": "https://example.com/bitbucket/",
            "active": True,
            "events": ["repo:push"],
            "description": "WebHook Description",
        })
        updated_hook = hook.modify(
            hook.description,
            hook.url,
            False,
            hook.events)

        assert updated_hook.description == 'WebHook Description'
        assert updated_hook.url == 'https://example.com/bitbucket/'
        assert updated_hook.events == ['repo:push']
        assert not updated_hook.active

    @httpretty.activate
    def test_delete_webhook(self):
        url = (
            self.client.get_bitbucket_url() +
            '/2.0/repositories/pybitbucket/testing/hooks/' +
            self.hook_uuid)
        httpretty.register_uri(
            httpretty.DELETE,
            url,
            content_type='application/json',
            status=204)
        hook = Hook({
            "uuid": "{ec96bf6b-abb2-4f30-90b9-0178342c9fc5}",
            "links": {
                "self": {"href": url}
            },
            "url": "https://example.com/bitbucket/",
            "active": True,
            "events": ["repo:push"],
            "description": "WebHook Description",
        })
        updated_hook = hook.delete()
        assert not updated_hook
