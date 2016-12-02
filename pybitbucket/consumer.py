# -*- coding: utf-8 -*-

from __future__ import unicode_literals

"""
Defines the Consumer resource and registers the type with the Client.

Classes:
- PermissionScope: enumerates the possible scopes for an OAuth consumer.
- ConsumerPayload: encapsulates payload for creating
    and modifying consumers.
- Consumer: represents an OAuth consumer.
"""

from uritemplate import expand
from voluptuous import Schema, Required, Optional, In

from pybitbucket.bitbucket import BitbucketBase, Client, PayloadBuilder, Enum


class PermissionScope(Enum):
    EMAIL = 'email'
    ACCOUNT_READ = 'account'
    ACCOUNT_WRITE = 'account:write'
    TEAM_READ = 'team'
    TEAM_WRITE = 'team:write'
    REPOSITORY_READ = 'repository'
    REPOSITORY_WRITE = 'repository:write'
    REPOSITORY_ADMIN = 'repository:admin'
    PULLREQUEST_READ = 'pullrequest'
    PULLREQUEST_WRITE = 'pullrequest:write'
    ISSUE_READ = 'issue'
    ISSUE_WRITE = 'issue:write'
    WIKI = 'wiki'
    SNIPPET_READ = 'snippet'
    SNIPPET_WRITE = 'snippet:write'
    WEBHOOK = 'webhook'


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
        Optional('scopes'): [In(PermissionScope)],
        Optional('secret'): str,
        Optional('callback_url'): str,
        Optional('id'): int,
    })

    def __init__(
            self,
            payload=None,
            consumer_id=None):
        super(self.__class__, self).__init__(payload=payload)
        self._consumer_id = consumer_id

    @property
    def consumer_id(self):
        return self._consumer_id

    def add_consumer_id(self, consumer_id):
        new = self._payload.copy()
        new['id'] = consumer_id
        return ConsumerPayload(
            payload=new,
            consumer_id=consumer_id)

    def add_name(self, name):
        new = self._payload.copy()
        new['name'] = name
        return ConsumerPayload(
            payload=new,
            consumer_id=self.consumer_id)

    def add_description(self, description):
        new = self._payload.copy()
        new['description'] = description
        return ConsumerPayload(
            payload=new,
            consumer_id=self.consumer_id)

    def add_url(self, url):
        new = self._payload.copy()
        new['url'] = url
        return ConsumerPayload(
            payload=new,
            consumer_id=self.consumer_id)

    def add_key(self, key):
        new = self._payload.copy()
        new['key'] = key
        return ConsumerPayload(
            payload=new,
            consumer_id=self.consumer_id)

    def add_scope(self, scope):
        new = self._payload.copy()
        new_scopes = self._payload.get('scopes', [])
        if scope not in new_scopes:
            new_scopes.append(scope)
        new['scopes'] = new_scopes
        return ConsumerPayload(
            payload=new,
            consumer_id=self.consumer_id)

    def add_scopes(self, scopes):
        new = self._payload.copy()
        new_scopes = self._payload.get('scopes', [])
        for scope in scopes:
            if scope not in new_scopes:
                new_scopes.append(scope)
        new['scopes'] = new_scopes
        return ConsumerPayload(
            payload=new,
            consumer_id=self.consumer_id)

    def add_secret(self, secret):
        new = self._payload.copy()
        new['secret'] = secret
        return ConsumerPayload(
            payload=new,
            consumer_id=self.consumer_id)

    def add_callback_url(self, callback_url):
        new = self._payload.copy()
        new['callback_url'] = callback_url
        return ConsumerPayload(
            payload=new,
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

    @classmethod
    def create(
            cls,
            payload,
            client=None):
        """Create a new consumer.

        :param payload: the options for creating the new consumer
        :type payload: ConsumerPayload
        :param client: the configured connection to Bitbucket.
            If not provided, assumes an Anonymous connection.
        :type client: bitbucket.Client
        :returns: the new consumer object.
        :rtype: Consumer
        :raises: ValueError
        """
        client = client or Client()
        owner = client.get_username()
        if not owner:
            raise ValueError('owner is required')
        data = payload.validate().build()
        templates = cls.extract_templates_from_json()
        api_url = expand(
            templates['create'], {
                'bitbucket_url': client.get_bitbucket_url(),
                'username': owner
            })
        # Note: This Bitbucket API expects a urlencoded-form, not json.
        # Hence, use `data` instead of `json`.
        return cls.post(api_url, data=data, client=client)

    def update(
            self,
            payload):
        """Update current consumer.

        :param payload: the options for updating the new consumer
        :type payload: ConsumerPayload
        :returns: the new consumer object.
        :rtype: Consumer
        :raises: ValueError
        """
        # Note: The Bitbucket API expects a urlencoded-form, not json.
        # Hence, use `data` instead of `json`.
        return self.put(data=payload.validate().build())

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
