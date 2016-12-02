# -*- coding: utf-8 -*-

from __future__ import unicode_literals

"""
Defines the BuildStatus resource and registers the type with the Client.

Classes:
- BuildStatusStates: enumerates the possible states of a build status
- BuildStatusPayload: encapsulates payload for creating
    and modifying build status
- BuildStatus: represents the result of a build
"""

from uritemplate import expand
from voluptuous import Schema, Required, Optional, In, Url

from pybitbucket.bitbucket import (
    Bitbucket, BitbucketBase, Client, PayloadBuilder, Enum)


class BuildStatusStates(Enum):
    INPROGRESS = 'INPROGRESS'
    SUCCESSFUL = 'SUCCESSFUL'
    FAILED = 'FAILED'


class BuildStatusPayload(PayloadBuilder):
    """
    A builder object to help create payloads
    for creating and updating build statuses.
    """

    schema = Schema({
        Required('key'): str,
        Required('state'): In(list(BuildStatusStates)),
        Required('url'): Url(),
        Optional('name'): str,
        Optional('description'): str
    })

    def __init__(
            self,
            payload=None,
            owner=None,
            repository_name=None,
            revision=None):
        super(self.__class__, self).__init__(payload=payload)
        self._owner = owner
        self._repository_name = repository_name
        self._revision = revision

    @property
    def owner(self):
        return self._owner

    @property
    def repository_name(self):
        return self._repository_name

    @property
    def revision(self):
        return self._revision

    def add_owner(self, owner):
        return BuildStatusPayload(
            payload=self._payload.copy(),
            owner=owner,
            repository_name=self.repository_name,
            revision=self.revision)

    def add_repository_name(self, repository_name):
        return BuildStatusPayload(
            payload=self._payload.copy(),
            owner=self.owner,
            repository_name=repository_name,
            revision=self.revision)

    def add_revision(self, revision):
        return BuildStatusPayload(
            payload=self._payload.copy(),
            owner=self.owner,
            repository_name=self.repository_name,
            revision=revision)

    def add_name(self, name):
        new = self._payload.copy()
        new['name'] = name
        return BuildStatusPayload(
            payload=new,
            owner=self.owner,
            repository_name=self.repository_name,
            revision=self.revision)

    def add_description(self, description):
        new = self._payload.copy()
        new['description'] = description
        return BuildStatusPayload(
            payload=new,
            owner=self.owner,
            repository_name=self.repository_name,
            revision=self.revision)

    def add_key(self, key):
        new = self._payload.copy()
        new['key'] = key
        return BuildStatusPayload(
            payload=new,
            owner=self.owner,
            repository_name=self.repository_name,
            revision=self.revision)

    def add_state(self, state):
        new = self._payload.copy()
        new['state'] = state
        return BuildStatusPayload(
            payload=new,
            owner=self.owner,
            repository_name=self.repository_name,
            revision=self.revision)

    def add_url(self, url):
        new = self._payload.copy()
        new['url'] = url
        return BuildStatusPayload(
            payload=new,
            owner=self.owner,
            repository_name=self.repository_name,
            revision=self.revision)


class BuildStatus(BitbucketBase):
    """Represents a build status."""

    id_attribute = 'key'
    resource_type = 'build'
    templates = {
        'create': (
            '{+bitbucket_url}' +
            '/2.0/repositories{/owner,repository_name}' +
            '/commit{/revision}/statuses/build')
    }

    @staticmethod
    def is_type(data):
        return (BuildStatus.has_v2_self_url(data))

    @classmethod
    def create(
            cls,
            payload,
            revision=None,
            repository_name=None,
            owner=None,
            client=None):
        """Create a new build status.

        :param payload: the options for creating the new build status.
        :type payload: BuildStatusPayload
        :param revision: revision in the repository,
            also known as commit. Optional, if provided in the payload.
        :type revision: str
        :param repository_name: name of the repository,
            also known as repo_slug. Optional, if provided in the payload.
        :type repository_name: str
        :param owner: the owner of the repository.
            If not provided as parameter, it may be provided in the payload.
            If neither, assume the current user.
        :type owner: str
        :param client: the configured connection to Bitbucket.
            If not provided, assumes an Anonymous connection.
        :type client: bitbucket.Client
        :returns: the new build status object.
        :rtype: BuildStatus
        :raises: ValueError
        """
        client = client or Client()
        owner = owner or payload.owner or client.get_username()
        repository_name = repository_name or payload.repository_name
        revision = revision or payload.revision
        if not (owner and repository_name and revision):
            raise ValueError(
                'owner, repository_name, and revision'
                ' are required')
        json = payload.validate().build()
        api_url = expand(
            cls.templates['create'], {
                'bitbucket_url': client.get_bitbucket_url(),
                'owner': owner,
                'repository_name': repository_name,
                'revision': revision
            })
        return cls.post(api_url, json=json, client=client)

    def modify(self, payload):
        """
        A convenience method for changing the current build status.
        """
        return self.put(json=payload.validate().build())

    @staticmethod
    def find_buildstatus_for_repository_commit_by_key(
            repository_name,
            revision,
            key,
            owner=None,
            client=None):
        """
        A convenience method for finding a specific build status.
        In contrast to the pure hypermedia driven method on the Bitbucket
        class, this method returns a BuildStatus object, instead of the
        generator.
        """
        client = client or Client()
        owner = owner or client.get_username()
        return next(
            Bitbucket(client=client).repositoryCommitBuildStatusByKey(
                owner=owner,
                repository_name=repository_name,
                revision=revision,
                key=key))

    @staticmethod
    def find_buildstatuses_for_repository_commit(
            repository_name,
            revision,
            owner=None,
            client=None):
        """
        A convenience method for finding build statuses
        for a repository's commit.
        The method is a generator BuildStatus objects.
        """
        client = client or Client()
        owner = owner or client.get_username()
        return Bitbucket(client=client).repositoryCommitBuildStatuses(
            owner=owner,
            repository_name=repository_name,
            revision=revision)


Client.bitbucket_types.add(BuildStatus)
