# -*- coding: utf-8 -*-

from __future__ import unicode_literals

"""
Defines the PullRequest resource and registers the type with the Client.

Classes:
- PullRequestState: enumerates the possible states of a pull request
- PullRequestPayload: encapsulates payload for creating
    and modifying pull requests
- PullRequest: represents a pull request for code review
"""

from functools import partial
from uritemplate import expand
from voluptuous import Schema, Required, Optional

from pybitbucket.bitbucket import (
        Bitbucket, BitbucketBase, Client, PayloadBuilder, Enum)


class PullRequestState(Enum):
    OPEN = 'OPEN'
    MERGED = 'MERGED'
    DECLINED = 'DECLINED'


class PullRequestPayload(PayloadBuilder):
    """
    A builder object to help create payloads
    for creating and updating pull requests.
    """

    schema = Schema({
        Required('title'): str,
        Optional('description'): str,
        Optional('close_source_branch'): bool,
        Optional('reviewers'): [{Required('username'): str}],
        Required('destination'): {
            Required('branch'): {
                Required('name'): str
            },
            Optional('commit'): {
                Required('hash'): str
            }
        },
        Required('source'): {
            Required('branch'): {
                Required('name'): str
            },
            Required('repository'): {
                Required('full_name'): str
            },
            Optional('commit'): {
                Required('hash'): str
            }
        }
    })

    def __init__(
            self,
            payload=None,
            destination_repository_owner=None,
            destination_repository_name=None):
        super(self.__class__, self).__init__(payload=payload)
        self._destination_repository_owner = destination_repository_owner
        self._destination_repository_name = destination_repository_name

    @property
    def destination_repository_owner(self):
        return self._destination_repository_owner

    @property
    def destination_repository_name(self):
        return self._destination_repository_name

    def add_title(self, title):
        new = self._payload.copy()
        new['title'] = title
        return PullRequestPayload(
            payload=new,
            destination_repository_owner=self._destination_repository_owner,
            destination_repository_name=self._destination_repository_name)

    def add_description(self, description):
        new = self._payload.copy()
        new['description'] = description
        return PullRequestPayload(
            payload=new,
            destination_repository_owner=self._destination_repository_owner,
            destination_repository_name=self._destination_repository_name)

    def add_close_source_branch(self, close):
        new = self._payload.copy()
        new['close_source_branch'] = close
        return PullRequestPayload(
            payload=new,
            destination_repository_owner=self._destination_repository_owner,
            destination_repository_name=self._destination_repository_name)

    def add_reviewer_by_username(self, username):
        new = self._payload.copy()
        reviewers = self._payload.get('reviewers', [])
        if {'username': username} not in reviewers:
            reviewers.append({'username': username})
        new['reviewers'] = reviewers
        return PullRequestPayload(
            payload=new,
            destination_repository_owner=self._destination_repository_owner,
            destination_repository_name=self._destination_repository_name)

    def add_reviewer(self, user):
        return self.add_reviewer_by_username(user.username)

    def add_reviewers_from_usernames(self, usernames):
        new = self._payload.copy()
        reviewers = self._payload.get('reviewers', [])
        for username in usernames:
            if {'username': username} not in reviewers:
                reviewers.append({'username': username})
        new['reviewers'] = reviewers
        return PullRequestPayload(
            payload=new,
            destination_repository_owner=self._destination_repository_owner,
            destination_repository_name=self._destination_repository_name)

    def add_destination_repository_owner(self, owner):
        return PullRequestPayload(
            payload=self._payload.copy(),
            destination_repository_owner=owner,
            destination_repository_name=self._destination_repository_name)

    def add_destination_repository_name(self, name):
        return PullRequestPayload(
            payload=self._payload.copy(),
            destination_repository_owner=self._destination_repository_owner,
            destination_repository_name=name)

    def add_destination_repository_full_name(self, full_name):
        owner, name = full_name.split('/', 1)
        return PullRequestPayload(
            payload=self._payload.copy(),
            destination_repository_owner=owner,
            destination_repository_name=name)

    def add_destination_repository(self, repository):
        owner, name = repository.full_name.split('/', 1)
        return PullRequestPayload(
            payload=self._payload.copy(),
            destination_repository_owner=owner,
            destination_repository_name=name)

    def add_destination_branch_name(self, name):
        new = self._payload.copy()
        destination = self._payload.get('destination', {})
        destination['branch'] = destination.get('branch', {})
        destination['branch']['name'] = name
        new['destination'] = destination
        return PullRequestPayload(
            payload=new,
            destination_repository_owner=self._destination_repository_owner,
            destination_repository_name=self._destination_repository_name)

    def add_destination_branch(self, branch):
        owner, name = branch.repository.full_name.split('/', 1)
        return PullRequestPayload(
                payload=self._payload.copy(),
                destination_repository_owner=owner,
                destination_repository_name=name) \
            .add_destination_branch_name(branch.name)

    def add_destination_commit_by_hash(self, hash):
        new = self._payload.copy()
        destination = self._payload.get('destination', {})
        destination['commit'] = destination.get('commit', {})
        destination['commit']['hash'] = hash
        new['destination'] = destination
        return PullRequestPayload(
            payload=new,
            destination_repository_owner=self._destination_repository_owner,
            destination_repository_name=self._destination_repository_name)

    def add_destination_commit(self, commit):
        owner, name = commit.repository.full_name.split('/', 1)
        return PullRequestPayload(
                payload=self._payload.copy(),
                destination_repository_owner=owner,
                destination_repository_name=name) \
            .add_destination_commit_by_hash(commit.hash)

    def add_source_branch_name(self, name):
        new = self._payload.copy()
        source = self._payload.get('source', {})
        source['branch'] = source.get('branch', {})
        source['branch']['name'] = name
        new['source'] = source
        return PullRequestPayload(
            payload=new,
            destination_repository_owner=self._destination_repository_owner,
            destination_repository_name=self._destination_repository_name)

    def add_source_repository_full_name(self, full_name):
        new = self._payload.copy()
        source = self._payload.get('source', {})
        source['repository'] = source.get('repository', {})
        source['repository']['full_name'] = full_name
        new['source'] = source
        return PullRequestPayload(
            payload=new,
            destination_repository_owner=self._destination_repository_owner,
            destination_repository_name=self._destination_repository_name)

    def add_source_branch(self, branch):
        return self.add_source_branch_name(branch.name) \
            .add_source_repository_full_name(branch.repository.full_name)

    def add_source_commit_by_hash(self, hash):
        new = self._payload.copy()
        source = self._payload.get('source', {})
        source['commit'] = source.get('commit', {})
        source['commit']['hash'] = hash
        new['source'] = source
        return PullRequestPayload(
            payload=new,
            destination_repository_owner=self._destination_repository_owner,
            destination_repository_name=self._destination_repository_name)

    def add_source_commit(self, commit):
        return self.add_source_commit_by_hash(commit.hash) \
            .add_source_repository_full_name(commit.repository.full_name)


class PullRequest(BitbucketBase):
    id_attribute = 'id'
    resource_type = 'pullrequests'
    templates = {
        'create': (
            '{+bitbucket_url}' +
            '/2.0/repositories' +
            '{/owner,repository_name}' +
            '/pullrequests')
    }

    @staticmethod
    def is_type(data):
        return (PullRequest.has_v2_self_url(data))

    def attr_from_subchild(self, target_attribute, child, child_object):
        if self.data.get(child, {}).get(child_object, {}):
            setattr(
                self,
                target_attribute,
                self.client.convert_to_object(
                    self.data[child][child_object]))

    def __init__(self, data, client=Client()):
        super(PullRequest, self).__init__(data, client=client)
        self.attr_from_subchild(
            'source_commit', 'source', 'commit')
        self.attr_from_subchild(
            'source_repository', 'source', 'repository')
        self.attr_from_subchild(
            'destination_commit', 'destination', 'commit')
        self.attr_from_subchild(
            'destination_repository', 'destination', 'repository')
        # Special treatment for approve, decline, merge, and diff
        if data.get('links', {}).get('approve', {}).get('href', {}):
            url = data['links']['approve']['href']
            # Approve is a POST on the approve link
            setattr(self, 'approve', partial(
                self.post_approval, template=url))
            # Unapprove is a DELETE on the approve link
            setattr(self, 'unapprove', partial(
                self.delete_approval, template=url))
        if data.get('links', {}).get('decline', {}).get('href', {}):
            url = data['links']['decline']['href']
            # Decline is a POST
            setattr(self, 'decline', partial(
                self.post, client=client, url=url, json=None))
        if data.get('links', {}).get('merge', {}).get('href', {}):
            url = data['links']['merge']['href']
            # Merge is a POST
            setattr(self, 'merge', partial(
                self.post, client=client, url=url, json=None))
        if data.get('links', {}).get('diff', {}).get('href', {}):
            url = data['links']['diff']['href']
            # Diff returns plain text
            setattr(self, 'diff', partial(
                self.content, url=url))

    def content(self, url):
        response = self.client.session.get(url)
        Client.expect_ok(response)
        return response.content

    @classmethod
    def create(
            cls,
            payload,
            repository_name=None,
            owner=None,
            client=None):
        """Create a new Pull Request.

        :param payload: the options for creating the new Pull Request
        :type payload: PullRequestPayload
        :param repository_name: name of the destination repository,
            also known as repo_slug. Optional, if provided in the payload.
        :type repository_name: str
        :param owner: the owner of the destination repository.
            Optional, if provided in the payload.
        :type owner: str
        :param client: the configured connection to Bitbucket.
            If not provided, assumes an Anonymous connection.
        :type client: bitbucket.Client
        :returns: the new repository object.
        :rtype: PullRequest
        :raises: ValueError
        """
        client = client or Client()
        owner = (
            owner or
            payload.destination_repository_owner)
        repository_name = (
            repository_name or
            payload.destination_repository_name)
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

    @staticmethod
    def find_pullrequest_by_id_in_repository(
            pullrequest_id,
            repository_name,
            owner=None,
            client=None):
        """
        A convenience method for finding a specific pull request.
        In contrast to the pure hypermedia driven method on the Bitbucket
        class, this method returns a PullRequest object, instead of the
        generator.
        """
        client = client or Client()
        owner = owner or client.get_username()
        return next(
            Bitbucket(client=client).repositoryPullRequestByPullRequestId(
                owner=owner,
                repository_name=repository_name,
                pullrequest_id=pullrequest_id))

    @staticmethod
    def find_pullrequests_for_repository_by_state(
            repository_name,
            owner=None,
            state=None,
            client=None):
        """
        A convenience method for finding pull requests for a repository.
        The method is a generator PullRequest objects.
        If no owner is provided, this method assumes client can provide one.
        If no state is provided, the server will assume open pull requests.
        """
        client = client or Client()
        owner = owner or client.get_username()
        if (state is not None):
            PullRequestState(state)
        return Bitbucket(client=client).repositoryPullRequestsInState(
            owner=owner,
            repository_name=repository_name,
            state=state)


Client.bitbucket_types.add(PullRequest)
