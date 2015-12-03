# -*- coding: utf-8 -*-
"""
Core classes for communicating with the Bitbucket API.

Classes:
- Config: prototype for HTTP connection information
- Client: abstraction over HTTP requests to Bitbucket API
- BitbucketBase: parent class for Bitbucket resources
- BadRequestError: exception wrapping bad HTTP requests
- ServerError: exception wrapping server errors
"""
import json
from future.utils import python_2_unicode_compatible
from functools import partial
from requests import codes
from requests.exceptions import HTTPError
from uritemplate import expand

from pybitbucket.auth import Anonymous
from pybitbucket.entrypoints import entrypoints_json


class Client(object):
    bitbucket_types = set()

    @staticmethod
    def expect_ok(response, code=codes.ok):
        if code == response.status_code:
            return
        elif 400 == response.status_code:
            raise BadRequestError(response)
        elif 500 <= response.status_code:
            raise ServerError(response)
        else:
            response.raise_for_status()

    def convert_to_object(self, data):
        for t in Client.bitbucket_types:
            if t.is_type(data):
                return t(data, client=self)
        return data

    def remote_relationship(self, template, **keywords):
        url = expand(template, keywords)
        while url:
            response = self.session.get(url)
            self.expect_ok(response)
            json_data = response.json()
            if json_data.get('page'):
                for item in json_data.get('values'):
                    yield self.convert_to_object(item)
            else:
                yield self.convert_to_object(json_data)
            url = json_data.get('next')

    def get_bitbucket_url(self):
        return self.config.server_base_uri

    def get_username(self):
        return self.config.username

    def __init__(self, config=None):
        self.config = config or Anonymous()
        self.session = self.config.session


@python_2_unicode_compatible
class BitbucketBase(object):
    id_attribute = 'id'

    @staticmethod
    def links_from(data):
        links = {}
        # Bitbucket doesn't currently use underscore.
        # HAL JSON does use underscore.
        for link_name in ('links', '_links'):
            if data.get(link_name):
                links.update(data.get(link_name))
        for name, body in links.items():
            # Ignore quirky Bitbucket clone link
            if isinstance(body, dict):
                for href, url in body.items():
                    if href == 'href':
                        yield (name, url)

    def add_remote_relationship_methods(self, data):
        for name, url in BitbucketBase.links_from(data):
            setattr(self, name, partial(
                self.client.remote_relationship,
                template=url))

    def __init__(self, data, client=Client()):
        self.data = data
        self.client = client
        self.__dict__.update(data)
        self.add_remote_relationship_methods(data)

    def delete(self):
        response = self.client.session.delete(self.links['self']['href'])
        # Deletes the resource and returns 204 (No Content).
        Client.expect_ok(response, 204)
        return

    def put(self, data, **kwargs):
        response = self.client.session.put(
            self.links['self']['href'],
            data=data,
            **kwargs)
        Client.expect_ok(response)
        return self.client.convert_to_object(response.json())

    def post(self, url, data, **kwargs):
        response = self.client.session.post(
            url,
            data=data,
            **kwargs)
        Client.expect_ok(response)
        return self.client.convert_to_object(response.json())

    def attributes(self):
        return list(self.data.keys())

    def relationships(self):
        return list(self.data['links'].keys())

    def __repr__(self):
        return u'{name}({data})'.format(
            name=type(self).__name__,
            data=repr(self.data))

    def __str__(self):
        return u'{name} {id}:{data}'.format(
            name=type(self).__name__,
            id=self.id_attribute,
            data=getattr(self, self.id_attribute))


class Bitbucket(BitbucketBase):
    def __init__(self, client=Client()):
        self.client = client
        self.add_remote_relationship_methods(
            json.loads(entrypoints_json))


class BitbucketError(HTTPError):
    interpretation = "The client encountered an error."

    def formatMessage(self):
        return u'''Attempted to request {url}. \
{interpretation} {code} - {text}\
'''.format(
            url=self.url,
            interpretation=self.interpretation,
            code=self.code,
            text=self.text)

    def __init__(self, response):
        self.url = response.url
        self.code = response.status_code
        self.text = response.text
        try:
            # if the response is json,
            # then make it part of the exception structure
            json_data = response.json()
            json_error_message = json_data.get('error').get('message')
            self.error_message = json_error_message
            self.__dict__.update(json_data)
        except ValueError:
            pass
        super(BitbucketError, self).__init__(
            self.formatMessage())


class BadRequestError(BitbucketError):
    interpretation = "Bitbucket considered it a bad request."

    def __init__(self, response):
        super(BadRequestError, self).__init__(response)


class ServerError(BitbucketError):
    interpretation = "The client encountered a server error."

    def __init__(self, response):
        super(ServerError, self).__init__(response)
