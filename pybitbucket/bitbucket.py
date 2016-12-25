# -*- coding: utf-8 -*-

from __future__ import unicode_literals

"""
Core classes for communicating with the Bitbucket API.

Classes:
- Enumeration: abstraction for a set of enumerated values
- Client: abstraction over HTTP requests to Bitbucket API
- BitbucketSpecialAction: an enum of special actions to be handled by children
- RepositoryType: an enum of repository types (Git, Hg)
- BitbucketBase: parent class for Bitbucket resources
- PayloadBuilder: parent class for payloads
- Bitbucket: root resource for the whole Bitbucket instance
- BadRequestError: exception wrapping bad HTTP requests
- ServerError: exception wrapping server errors
"""

from enum import Enum as EnumBase
from json import loads, dumps, JSONEncoder as JSONEncoderBase
from functools import partial
from requests import codes, models as requests_models
from requests.exceptions import HTTPError
from uritemplate import expand
from voluptuous import Schema

from pybitbucket.auth import Anonymous
from pybitbucket.entrypoints import entrypoints_json


# subclass Enum to make it behave the same way as the former custom Enum class
class Enum(EnumBase):
    def __eq__(self, o):
        return self is o or self.__class__(o).value == self.value


class JSONEncoder(JSONEncoderBase):
    def default(self, obj):
        if isinstance(obj, Enum):
            return obj.value
        return super(JSONEncoder, self).default(obj)


# monkey patch request's json handler
requests_models.complexjson.dumps = partial(dumps, cls=JSONEncoder)


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
        if isinstance(data, Enum):
            return data.value()
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
            if isinstance(json_data, list):
                for item in json_data:
                    yield self.convert_to_object(item)
                url = None
            elif json_data.get('values'):
                for item in json_data['values']:
                    yield self.convert_to_object(item)
                url = json_data.get('next')
            else:
                yield self.convert_to_object(json_data)
                url = None

    def get_bitbucket_url(self):
        return self.config.server_base_uri

    def get_username(self):
        return self.config.get_username()

    def __init__(self, config=None):
        self.config = config or Anonymous()
        self.session = self.config.session


class BitbucketSpecialAction(Enum):
    APPROVE = 'approve'
    DECLINE = 'decline'
    MERGE = 'merge'
    DIFF = 'diff'


class RepositoryType(Enum):
    GIT = 'git'
    HG = 'hg'


class BitbucketBase(object):
    id_attribute = 'id'

    @staticmethod
    def expect_bool(name, value):
        if not isinstance(value, bool):
            raise TypeError(
                "{0} is {1} instead of bool".format(name, type(value)))

    @staticmethod
    def expect_list(name, value):
        if not isinstance(value, (list, tuple)):
            raise TypeError(
                "{0} is {1} instead of list".format(name, type(value)))

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

    @staticmethod
    def _has_v2_self_url(data, resource_type, id_attribute):
        if (
                (data.get('links') is None) or
                (data['links'].get('self') is None) or
                (data['links']['self'].get('href') is None) or
                (data.get(id_attribute) is None)):
            return False
        # Since the structure is right, assume it is v2.
        is_v2 = True
        url_path = data['links']['self']['href'].split('/')
        # Start looking from the end of the path.
        position = -1
        # Since repos have a slash in the full_name,
        # we have to match as many parts as we find (1 or 2).
        # And sometimes the id is an integer.
        for id_part in str(data[id_attribute]).split('/')[::-1]:
            is_v2 = is_v2 and (id_part == url_path[position])
            position -= 1
        # After matching the id_attribute,
        # the resource_type should be the preceding part of the path.
        is_v2 = (resource_type == url_path[position])
        return is_v2

    @classmethod
    def has_v2_self_url(cls, data):
        return cls._has_v2_self_url(data, cls.resource_type, cls.id_attribute)

    def add_remote_relationship_methods(self, data):
        for name, url in BitbucketBase.links_from(data):
            if (name not in BitbucketSpecialAction):
                setattr(self, name, partial(
                    self.client.remote_relationship,
                    template=url))

    def add_inline_resources(self, data):
        for name, body in data.items():
            # author is not treated the same on all resources
            if name == 'author':
                # For Commits, author has a raw part and
                # a full User resource.
                if (body.get('raw') and body.get('user')):
                    setattr(self, 'raw_author', body['raw'])
                    setattr(self, 'author', self.client.convert_to_object(
                        body['user']))
                # For PullRequests, author is just a User resource.
                else:
                    setattr(self, name, self.client.convert_to_object(body))
            # If an attribute has a dictionary for a body,
            # then descend to check for embedded resources.
            elif isinstance(body, dict):
                setattr(self, name, self.client.convert_to_object(body))
            # If an attribute has a list for a body,
            # then descend into the array to check for embedded resources.
            elif isinstance(body, list):
                if (body and isinstance(body[0], dict)):
                    setattr(self, name, [
                        self.client.convert_to_object(i)
                        for i in body])
                else:
                    setattr(self, name, body)

    @classmethod
    def extract_templates_from_json(cls):
        """
        A helper method for 1.0 API resources that extracts uri templates
        found in links into a template that would be found
        on a 2.0 API resource.
        """
        links = loads(cls.links_json)
        return {
            name: url
            for (name, url)
            in cls.links_from(links)}

    @classmethod
    def expand_link_urls(cls, **kwargs):
        """
        A helper method for 1.0 API resources that expands uri templates
        found in links into a fully navigable URL as would be found
        with a HAL-JSON resource.
        """
        links = loads(cls.links_json)
        return {'_links': {
            name: {'href': expand(template, kwargs)}
            for (name, template)
            in cls.links_from(links)}}

    @classmethod
    def get_link_template(cls, name):
        """
        A helper method for 1.0 API resources that gets the raw uri template
        for a specific link.
        """
        links = loads(cls.links_json)
        templates = [v for k, v in cls.links_from(links) if k == name]
        return templates[0]

    def __init__(self, data, client=Client()):
        self.data = data
        self.client = client
        self.__dict__.update(data)
        self.add_remote_relationship_methods(data)
        self.add_inline_resources(data)

    def delete(self):
        url = self.links['self']['href']
        response = self.client.session.delete(url)
        # Deletes the resource and returns 204 (No Content).
        Client.expect_ok(response, 204)
        return

    def put(self, json=None, **kwargs):
        url = self.links['self']['href']
        response = self.client.session.put(url, json=json, **kwargs)
        Client.expect_ok(response)
        return self.client.convert_to_object(response.json())

    @staticmethod
    def post(url, json=None, data=None, client=Client(), **kwargs):
        if data:
            response = client.session.post(url, data=data, **kwargs)
        else:
            response = client.session.post(url, json=json, **kwargs)
        Client.expect_ok(response)
        return client.convert_to_object(response.json())

    def post_approval(self, template):
        response = self.client.session.post(template)
        Client.expect_ok(response)
        json_data = response.json()
        return json_data.get('approved')

    def delete_approval(self, template):
        response = self.client.session.delete(template)
        # Deletes the approval and returns 204 (No Content).
        Client.expect_ok(response, 204)
        return True

    def attributes(self):
        return list(self.data.keys())

    def relationships(self):
        return (
            list(self.data.get('_links', {}).keys()) +
            list(self.data.get('links', {}).keys()))

    def __repr__(self):
        return u'{name}({data})'.format(
            name=type(self).__name__,
            data=repr(self.data))

    def __str__(self):
        return u'{name} {id}:{data}'.format(
            name=type(self).__name__,
            id=self.id_attribute,
            data=getattr(self, self.id_attribute))


class PayloadBuilder(object):
    schema = Schema({})

    def __init__(self, payload=None):
        self._payload = payload or {}

    def build(self):
        payload = {}
        for k, v in self._payload.items():
            if isinstance(v, Enum):
                payload[k] = v.value
            else:
                payload[k] = v
        return payload

    def validate(self):
        self.schema(self._payload)
        return self


class Bitbucket(BitbucketBase):
    def __init__(self, client=Client()):
        self.data = loads(entrypoints_json)
        self.client = client
        self.add_remote_relationship_methods(self.data)


class BitbucketError(HTTPError):
    """Raise when Bitbucket has an HTTP error."""
    interpretation = "The client encountered an error."

    def format_message(self):
        return ('Attempted to request {url}.'
                '{interpretation} {code} - {text}').format(
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
            self.format_message())


class BadRequestError(BitbucketError):
    """Raise when Bitbucket complains about a bad request."""
    interpretation = "Bitbucket considered it a bad request."

    def __init__(self, response):
        super(BadRequestError, self).__init__(response)


class ServerError(BitbucketError):
    """Raise when Bitbucket complains about a server error."""
    interpretation = "The client encountered a server error."

    def __init__(self, response):
        super(ServerError, self).__init__(response)

from pybitbucket.repository import Repository
from pybitbucket.branchrestriction import BranchRestriction
from pybitbucket.build import BuildStatus
from pybitbucket.comment import Comment
from pybitbucket.commit import Commit
from pybitbucket.consumer import Consumer
from pybitbucket.hook import Hook
from pybitbucket.pullrequest import PullRequest
from pybitbucket.ref import Ref
from pybitbucket.snippet import Snippet
from pybitbucket.team import Team
from pybitbucket.user import User
