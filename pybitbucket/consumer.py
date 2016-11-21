# -*- coding: utf-8 -*-
"""
Defines the Consumer resource and registers the type with the Client.

Classes:
- PermissionScope: enumerates the possible scopes for an OAuth consumer.
- ConsumerPayload: encapsulates payload for creating
    and modifying consumers.
- Consumer: represents an OAuth consumer.
"""
from uritemplate import expand
from voluptuous import Schema, Required, Optional

from pybitbucket.bitbucket import (
    BitbucketBase, Client, enum, PayloadBuilder)


PermissionScope = enum(
    'PermissionScope',
    EMAIL='email',
    ACCOUNT_READ='account',
    ACCOUNT_WRITE='account:write',
    TEAM_READ='team',
    TEAM_WRITE='team:write',
    REPOSITORY_READ='repository',
    REPOSITORY_WRITE='repository:write',
    REPOSITORY_ADMIN='repository:admin',
    PULLREQUEST_READ='pullrequest',
    PULLREQUEST_WRITE='pullrequest:write',
    ISSUE_READ='issue',
    ISSUE_WRITE='issue:write',
    WIKI='wiki',
    SNIPPET_READ='snippet',
    SNIPPET_WRITE='snippet:write',
    WEBHOOK='webhook')


class ConsumerPayload(PayloadBuilder):
    """
    A builder object to help create payloads
    for creating and updating consumers.
    """

    schema = Schema({
        Required('name'): str,
        Optional('description'): str,
        Optional('url'): str,
        Optional('key'): str,
        # Undocumented attributes
        Optional('secret'): str,
        Optional('callback_url'): str,
        Optional('id'): int,
    })

    def __init__(
            self,
            payload=None,
            owner=None,
            consumer_id=None):
        super(self.__class__, self).__init__(payload=payload)
        self._owner = owner
        self._consumer_id = consumer_id

    @property
    def owner(self):
        return self._owner

    @property
    def consumer_id(self):
        return self._consumer_id

    def add_owner(self, owner):
        return ConsumerPayload(
            payload=self._payload.copy(),
            owner=owner,
            consumer_id=self._consumer_id)

    def add_consumer_id(self, consumer_id):
        new = self._payload.copy()
        new['id'] = consumer_id
        return ConsumerPayload(
            payload=new,
            owner=self.owner,
            consumer_id=consumer_id)

    def add_name(self, name):
        new = self._payload.copy()
        new['name'] = name
        return ConsumerPayload(
            payload=new,
            owner=self.owner,
            consumer_id=self.consumer_id)

    def copy_all_but_payload(self, new_payload):
        return self.__class__(
            payload=new_payload,
            owner=self.owner,
            consumer_id=self.consumer_id)

    def add_string_attribute(self, attribute_name, value):
        new = self._payload.copy()
        new[attribute_name] = value
        return self.copy_all_but_payload(new)

    def add_description(self, description):
        new = self._payload.copy()
        new['description'] = description
        return ConsumerPayload(
            payload=new,
            owner=self.owner,
            consumer_id=self.consumer_id)

    def add_url(self, url):
        new = self._payload.copy()
        new['url'] = url
        return ConsumerPayload(
            payload=new,
            owner=self.owner,
            consumer_id=self.consumer_id)

    def add_key(self, key):
        new = self._payload.copy()
        new['key'] = key
        return ConsumerPayload(
            payload=new,
            owner=self.owner,
            consumer_id=self.consumer_id)

    def add_secret(self, secret):
        new = self._payload.copy()
        new['secret'] = secret
        return ConsumerPayload(
            payload=new,
            owner=self.owner,
            consumer_id=self.consumer_id)

    def add_callback_url(self, callback_url):
        new = self._payload.copy()
        new['callback_url'] = callback_url
        return ConsumerPayload(
            payload=new,
            owner=self.owner,
            consumer_id=self.consumer_id)


class Consumer(BitbucketBase):
    id_attribute = 'id'
    links_json = """
{
  "_links": {
    "self": {
      "href": "{+bitbucket_url}/1.0/users{/username}/consumers{/consumer_id}"
    },
    "owner": {
      "href": "{+bitbucket_url}/1.0/users{/username}"
    },
    "consumers": {
      "href": "{+bitbucket_url}/1.0/users{/username}/consumers"
    },
    "create": {
      "href": "{+bitbucket_url}/1.0/users{/username}/consumers"
    }
  }
}
"""

    @staticmethod
    def is_type(data):
        return (
            (data.get('id') is not None) and
            (data.get('name') is not None) and
            (data.get('secret') is not None) and
            (data.get('key') is not None))

    def __init__(self, data={}, client=None):
        client = client or Client()
        super(Consumer, self).__init__(data, client=client)
        expanded_links = self.expand_link_urls(
            bitbucket_url=client.get_bitbucket_url(),
            username=client.get_username(),
            consumer_id=data.get('id'))
        self.links = expanded_links.get('_links', {})
        self.templates = self.extract_templates_from_json()
        self.add_remote_relationship_methods(expanded_links)

    # TODO: convert Consumer to PayloadBuilder pattern.
    @staticmethod
    def payload(
            name=None,
            scopes=None,
            description=None,
            url=None,
            callback_url=None):
        payload = []
        # Since server defaults may change, method defaults are None.
        # If the parameters are not provided, then don't send them
        # so the server can decide what defaults to use.
        if name is not None:
            payload.append(('name', name))
        if scopes is not None:
            Consumer.expect_list('scopes', scopes)
            [PermissionScope.expect_valid_value(s) for s in scopes]
            [payload.append(('scope', s)) for s in scopes]
        if description is not None:
            payload.append(('description', description))
        if url is not None:
            payload.append(('url', url))
        if callback_url is not None:
            payload.append(('callback_url', callback_url))
        return payload

    @staticmethod
    def create(
            name,
            scopes,
            description=None,
            url=None,
            callback_url=None,
            client=Client()):
        """
        A convenience method for creating a new consumer.
        The parameters make it easier to know what can be changed.
        Consumers can only be created for the currently authenticated user.
        """
        post_url = expand(
            Consumer.get_link_template('consumers'), {
                'bitbucket_url': client.get_bitbucket_url(),
                'username': client.get_username()
            })
        payload = Consumer.payload(
            name=name,
            scopes=scopes,
            description=description,
            url=url,
            callback_url=callback_url)
        # Note: The Bitbucket API expects a urlencoded-form, not json.
        # Hence, use `data` instead of `json`.
        return Consumer.post(post_url, data=payload, client=client)

    def update(
            self,
            name=None,
            scopes=None,
            description=None,
            url=None,
            callback_url=None):
        """
        A convenience method for changing the current consumer.
        The parameters make it easier to know what can be changed.
        Consumers can only be modified for the currently authenticated user.
        """
        kwargs = {k: v for k, v in locals().items() if k != 'self'}
        payload = self.payload(**kwargs)
        # Note: The Bitbucket API expects a urlencoded-form, not json.
        # Hence, use `data` instead of `json`.
        return self.put(data=payload)

    @staticmethod
    def find_consumers(client=Client()):
        """
        Find consumers for the authenticated user.
        The method is a generator Consumer objects.
        """
        url = expand(
            Consumer.get_link_template('consumers'), {
                'bitbucket_url': client.get_bitbucket_url(),
                'username': client.get_username()
            })
        return client.remote_relationship(url)

    @staticmethod
    def find_consumer_by_id(consumer_id, client=Client()):
        """
        Finding a specific consumer by id for the authenticated user.
        """
        url = expand(
            Consumer.get_link_template('self'), {
                'bitbucket_url': client.get_bitbucket_url(),
                'username': client.get_username(),
                'consumer_id': consumer_id,
            })
        return next(client.remote_relationship(url))


Client.bitbucket_types.add(Consumer)
