# -*- coding: utf-8 -*-

from __future__ import unicode_literals

"""
Defines the Hook resource and registers the type with the Client.

Classes:
- HookEvent: enumerates the possible events for subscription.
- HookPayload: encapsulates payload for creating
    and modifying hooks.
- Hook: represents a web hook for a repository
"""

from uritemplate import expand
from voluptuous import Schema, Required, Optional, In

from pybitbucket.bitbucket import (
    Bitbucket, BitbucketBase, Client, PayloadBuilder, Enum)


class HookEvent(Enum):
    REPOSITORY_PUSH = 'repo:push'
    REPOSITORY_FORK = 'repo:fork'
    REPOSITORY_UPDATED = 'repo:updated'
    REPOSITORY_COMMIT_COMMENT_CREATED = 'repo:commit_comment_created'
    REPOSITORY_BUILD_STATUS_CREATED = 'repo:commit_status_created'
    REPOSITORY_BUILD_STATUS_UPDATE = 'repo:commit_status_updated'
    ISSUE_CREATED = 'issue:created'
    ISSUE_UPDATED = 'issue:updated'
    ISSUE_COMMENT_CREATED = 'issue:comment_created'
    PULL_REQUEST_CREATED = 'pullrequest:created'
    PULL_REQUEST_UPDATED = 'pullrequest:updated'
    PULL_REQUEST_APPROVED = 'pullrequest:approved'
    PULL_REQUEST_APPROVAL_REMOVED = 'pullrequest:unapproved'
    PULL_REQUEST_MERGED = 'pullrequest:fulfilled'
    PULL_REQUEST_DECLINED = 'pullrequest:rejected'
    PULL_REQUEST_COMMENT_CREATED = 'pullrequest:comment_created'
    PULL_REQUEST_COMMENT_UPDATED = 'pullrequest:comment_updated'
    PULL_REQUEST_COMMENT_DELETED = 'pullrequest:comment_deleted'


class HookPayload(PayloadBuilder):
    """
    A builder object to help create payloads
    for creating and updating hooks.
    """

    schema = Schema({
        Required('description'): str,
        Required('url'): str,
        Optional('active'): bool,
        Optional('events'): [In(HookEvent)],
        # Undocumented attributes
        Optional('skip_cert_verification'): bool,
    })

    def __init__(
            self,
            payload=None,
            owner=None,
            repository_name=None):
        super(self.__class__, self).__init__(payload=payload)
        self._owner = owner
        self._repository_name = repository_name

    @property
    def owner(self):
        return self._owner

    @property
    def repository_name(self):
        return self._repository_name

    def add_owner(self, owner):
        return HookPayload(
            payload=self._payload.copy(),
            owner=owner,
            repository_name=self._repository_name)

    def add_repository_name(self, name):
        return HookPayload(
            payload=self._payload.copy(),
            owner=self._owner,
            repository_name=name)

    def add_repository_full_name(self, full_name):
        owner, name = full_name.split('/', 1)
        return HookPayload(
            payload=self._payload.copy(),
            owner=owner,
            repository_name=name)

    def add_description(self, description):
        new = self._payload.copy()
        new['description'] = description
        return HookPayload(
            payload=new,
            owner=self.owner,
            repository_name=self.repository_name)

    def add_callback_url(self, callback_url):
        new = self._payload.copy()
        new['url'] = callback_url
        return HookPayload(
            payload=new,
            owner=self.owner,
            repository_name=self.repository_name)

    def activate(self):
        new = self._payload.copy()
        new['active'] = True
        return HookPayload(
            payload=new,
            owner=self.owner,
            repository_name=self.repository_name)

    def deactivate(self):
        new = self._payload.copy()
        new['active'] = False
        return HookPayload(
            payload=new,
            owner=self.owner,
            repository_name=self.repository_name)

    def add_event(self, event):
        new = self._payload.copy()
        new_events = self._payload.get('events', [])
        if event not in new_events:
            new_events.append(event)
        new['events'] = new_events
        return HookPayload(
            payload=new,
            owner=self.owner,
            repository_name=self.repository_name)

    def add_events(self, events):
        new = self._payload.copy()
        new_events = self._payload.get('events', [])
        for event in events:
            if event not in new_events:
                new_events.append(event)
        new['events'] = new_events
        return HookPayload(
            payload=new,
            owner=self.owner,
            repository_name=self.repository_name)

    def enable_cert_verification(self):
        new = self._payload.copy()
        new['skip_cert_verification'] = False
        return HookPayload(
            payload=new,
            owner=self.owner,
            repository_name=self.repository_name)

    def disable_cert_verification(self):
        new = self._payload.copy()
        new['skip_cert_verification'] = True
        return HookPayload(
            payload=new,
            owner=self.owner,
            repository_name=self.repository_name)


class Hook(BitbucketBase):
    id_attribute = 'uuid'
    resource_type = 'hooks'
    templates = {
        'create': (
            '{+bitbucket_url}' +
            '/2.0/repositories' +
            '{/owner,repository_name}' +
            '/hooks')
    }

    @staticmethod
    def is_type(data):
        return (Hook.has_v2_self_url(data))

    @classmethod
    def create(
            cls,
            payload,
            repository_name=None,
            owner=None,
            client=None):
        """Create a new hook.

        :param payload: the options for creating the new hook
        :type payload: HookPayload
        :param repository_name: name of the repository,
            also known as repo_slug. Optional, if provided in the payload.
        :type repository_name: str
        :param owner: the owner of the repository.
            Optional, if provided in the payload.
            If not explicit as parameter or available in payload,
            uses the current user.
        :type owner: str
        :param client: the configured connection to Bitbucket.
            If not provided, assumes an Anonymous connection.
        :type client: bitbucket.Client
        :returns: the new hook object.
        :rtype: Hook
        :raises: MultipleInvalid
        """
        client = client or Client()
        owner = (
            owner or
            payload.owner or
            client.get_username())
        repository_name = (
            repository_name or
            payload.repository_name)
        if not (owner and repository_name):
            raise ValueError('owner and repository_name are required')
        json = payload.validate().build()
        api_url = expand(
            cls.templates['create'], {
                'bitbucket_url': client.get_bitbucket_url(),
                'owner': owner,
                'repository_name': repository_name,
            })
        return cls.post(api_url, json=json, client=client)

    def update(
            self,
            payload):
        """Update current hook.

        :param payload: the options for updating the new hook
        :type payload: HookPayload
        :returns: the new hook object.
        :rtype: Hook
        :raises: MultipleInvalid
        """
        return self.put(json=payload.validate().build())

    @staticmethod
    def find_hook_by_uuid_in_repository(
            uuid,
            repository_name,
            owner=None,
            client=None):
        """
        A convenience method for finding a specific hook.
        In contrast to the pure hypermedia driven method on the Bitbucket
        class, this method returns a Hook object, instead of the
        generator.
        """
        client = client or Client()
        owner = owner or client.get_username()
        return next(
            Bitbucket(client=client).repositoryHookById(
                owner=owner,
                repository_name=repository_name,
                uuid=uuid))

    @staticmethod
    def find_hooks_for_repository(
            repository_name,
            owner=None,
            client=None):
        """
        A convenience method for finding hooks for a repository.
        The method is a generator Hooks objects.
        If no owner is provided, this method assumes client can provide one.
        """
        client = client or Client()
        owner = owner or client.get_username()
        return Bitbucket(client=client).repositoryHooks(
            owner=owner,
            repository_name=repository_name)


Client.bitbucket_types.add(Hook)
