# -*- coding: utf-8 -*-

from __future__ import unicode_literals

"""
Defines the BranchRestriction resource and registers the type with the Client.

Classes:
- BranchRestrictionKind: enumerates the possible restrictions for a branch.
- BranchRestrictionPayload: encapsulates payload for creating
    and modifying branch restrictions.
- BranchRestriction: represents a restriction on a branch for a repository.
"""

from uritemplate import expand
from voluptuous import Schema, Required, Optional, In, Invalid

from pybitbucket.bitbucket import (
    Bitbucket, BitbucketBase, Client, PayloadBuilder, Enum)


class BranchRestrictionKind(Enum):
    PUSH = 'push'
    DELETE = 'delete'
    FORCE = 'force'


class BranchRestrictionPayload(PayloadBuilder):
    """
    A builder object to help create payloads
    for creating and updating branch restrictions.
    """

    schema = Schema({
        Required('kind'): In(BranchRestrictionKind),
        Optional('pattern'): str,
        Optional('groups'): [{
            Required('owner'):
                {Required('username'): str},
            Required('slug'): str,
        }],
        Optional('users'): [{Required('username'): str}],
    })

    def __init__(
            self,
            payload=None,
            owner=None,
            repository_name=None):
        super(BranchRestrictionPayload, self).__init__(payload=payload)
        self._owner = owner
        self._repository_name = repository_name

    @property
    def owner(self):
        return self._owner

    @property
    def repository_name(self):
        return self._repository_name

    def add_owner(self, owner):
        return BranchRestrictionPayload(
            payload=self._payload.copy(),
            owner=owner,
            repository_name=self.repository_name)

    def add_repository_name(self, repository_name):
        return BranchRestrictionPayload(
            payload=self._payload.copy(),
            owner=self.owner,
            repository_name=repository_name)

    def add_kind(self, kind):
        new = self._payload.copy()
        new['kind'] = kind
        return BranchRestrictionPayload(
            payload=new,
            owner=self.owner,
            repository_name=self.repository_name)

    def add_pattern(self, pattern):
        new = self._payload.copy()
        new['pattern'] = pattern
        return BranchRestrictionPayload(
            payload=new,
            owner=self.owner,
            repository_name=self.repository_name)

    # TODO: implement Group resource
    def add_group(self, group):
        return self.add_group_by_username_and_groupname(
            group.owner.username,
            group.name)

    def add_group_by_username_and_groupname(self, username, groupname):
        new = self._payload.copy()
        groups = self._payload.get('groups', [])
        groups.append({
            'owner': {'username': username},
            'slug': groupname})
        new['groups'] = groups
        return BranchRestrictionPayload(
            payload=new,
            owner=self.owner,
            repository_name=self.repository_name)

    def add_user(self, user):
        return self.add_user_by_username(user.username)

    def add_user_by_username(self, username):
        new = self._payload.copy()
        users = self._payload.get('users', [])
        users.append({'username': username})
        new['users'] = users
        return BranchRestrictionPayload(
            payload=new,
            owner=self.owner,
            repository_name=self.repository_name)

    def add_users_from_usernames(self, usernames):
        new = self._payload.copy()
        users = self._payload.get('users', [])
        for username in usernames:
            if {'username': username} not in users:
                users.append({'username': username})
        new['users'] = users
        return BranchRestrictionPayload(
            payload=new,
            owner=self.owner,
            repository_name=self.repository_name)


class BranchRestriction(BitbucketBase):
    id_attribute = 'id'
    resource_type = 'branch-restrictions'
    templates = {
        'create': (
            '{+bitbucket_url}' +
            '/2.0/repositories' +
            '{/owner,repository_name}' +
            '/branch-restrictions')
    }

    @staticmethod
    def is_type(data):
        return (BranchRestriction.has_v2_self_url(data))

    @classmethod
    def create(
            cls,
            payload,
            repository_name=None,
            owner=None,
            client=None):
        """Create a new branch-restriction.

        :param payload: the options for creating the new Branch Restriction
        :type payload: BranchRestrictionPayload
        :param repository_name: name of the destination repository,
            also known as repo_slug. Optional, if provided in the payload.
        :type repository_name: str
        :param owner: the owner of the destination repository.
            If not provided, assumes the current user.
        :type owner: str
        :param client: the configured connection to Bitbucket.
            If not provided, assumes an Anonymous connection.
        :type client: bitbucket.Client
        :returns: the new BranchRestriction object.
        :rtype: BranchRestriction
        :raises: MultipleInvalid, Invalid
        """
        client = client or Client()
        owner = owner or payload.owner
        repository_name = repository_name or payload.repository_name
        if not (owner and repository_name):
            raise Invalid('owner and repository_name are required')
        json = payload.validate().build()
        api_url = expand(
            cls.templates['create'], {
                'bitbucket_url': client.get_bitbucket_url(),
                'owner': owner,
                'repository_name': repository_name,
            })
        return cls.post(api_url, json=json, client=client)

    def modify(self, payload):
        """
        A convenience method for changing the current branch-restriction.
        The parameters make it easier to know what can be changed.
        """
        json = payload.validate().build()
        return self.put(json=json)

    @staticmethod
    def find_branchrestrictions_for_repository(
            repository_name,
            owner=None,
            client=None):
        """
        A convenience method for finding branch-restrictions for a repository.
        The method is a generator BranchRestriction objects.
        """
        client = client or Client()
        owner = owner or client.get_username()
        return Bitbucket(client=client).repositoryBranchRestrictions(
            owner=owner,
            repository_name=repository_name)

    @staticmethod
    def find_branchrestriction_for_repository_by_id(
            repository_name,
            restriction_id,
            owner=None,
            client=None):
        """
        A convenience method for finding a specific branch-restriction.
        In contrast to the pure hypermedia driven method on the Bitbucket
        class, this method returns a BranchRestriction object, instead of the
        generator.
        """
        client = client or Client()
        owner = owner or client.get_username()
        return next(
            Bitbucket(
                client=client).repositoryBranchRestrictionByRestrictionId(
                    owner=owner,
                    repository_name=repository_name,
                    restriction_id=restriction_id))


Client.bitbucket_types.add(BranchRestriction)
