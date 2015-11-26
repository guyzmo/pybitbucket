# -*- coding: utf-8 -*-
import httpretty

from test_client import TestConfig

from pybitbucket.bitbucket import Client
from pybitbucket.bitbucket import BadRequestError


class TestExceptions(object):

    @httpretty.activate
    def test_structured_exception(self):
        Client.configurator = TestConfig
        client = Client()
        http_error_code = 400
        url = 'https://' + client.get_bitbucket_url() + '/1.0/user'
        example = '''{"error": {"message": "Repository already exists."}}'''
        httpretty.register_uri(
            httpretty.GET,
            url,
            content_type='application/json',
            body=example,
            status=http_error_code)
        response = client.session.get(url)
        try:
            Client.expect_ok(response)
        except BadRequestError as b:
            assert b.url == url
            assert b.code == http_error_code
            assert b.error_message == "Repository already exists."
            assert list(b.error)
        else:
            assert False
