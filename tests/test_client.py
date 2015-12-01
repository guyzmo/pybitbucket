# -*- coding: utf-8 -*-
import httpretty

from pybitbucket.bitbucket import Client, BadRequestError, ServerError

from test_auth import TestAuth


class TestClient(object):

    @httpretty.activate
    def test_exceptions(self):
        a = TestAuth()
        session = a.start_http_session()

        httpretty.register_uri(
            httpretty.GET,
            a.server_base_uri,
            status=400)
        response = session.get(a.server_base_uri)
        try:
            raise BadRequestError(response)
        except BadRequestError as e:
            assert e
        else:
            assert False

        httpretty.register_uri(
            httpretty.GET,
            a.server_base_uri,
            status=500)
        response = session.get(a.server_base_uri)
        try:
            raise ServerError(response)
        except ServerError as e:
            assert e
        else:
            assert False

    @httpretty.activate
    def test_expect_ok(self):
        a = TestAuth()
        httpretty.register_uri(httpretty.GET, a.server_base_uri)
        session = a.start_http_session()
        response = session.get(a.server_base_uri)
        try:
            Client.expect_ok(response)
        except Exception:
            assert False

    @httpretty.activate
    def test_structured_exception(self):
        a = TestAuth()
        client = Client(a)
        http_error_code = 400
        url = a.server_base_uri + '/1.0/user'
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

    @httpretty.activate
    def test_client_construction(self):
        client = Client(TestAuth())
        assert 'https://staging.bitbucket.org/api' == \
            client.get_bitbucket_url()
        url = client.get_bitbucket_url() + '/1.0/user'
        httpretty.register_uri(httpretty.GET, url)
        response = client.session.get(url)
        assert 200 == response.status_code
