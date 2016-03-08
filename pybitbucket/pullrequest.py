# -*- coding: utf-8 -*-
"""
Defines the PullRequest resource and registers the type with the Client.

Classes:
- PullRequestState: enumerates the possible states of a pull request
- PullRequestPayload: a value type for creating and updating pull requests
- PullRequest: represents a pull request for code review
"""
from functools import partial
from uritemplate import expand

from pybitbucket.bitbucket import Bitbucket, BitbucketBase, Client, enum


PullRequestState = enum(
    'PullRequestState',
    OPEN='OPEN',
    MERGED='MERGED',
    DECLINED='DECLINED')


class PullRequestPayload(object):
    """A value type for creating and updating pull requests."""
    properties = [
        'title',
        'description',
        'reviewers',
        'close_source_branch',
        'source_repository_full_name',
        'source_branch_name',
        'source_commit',
        'destination_branch_name',
        'destination_commit']

    def __init__(self, **kwargs):
        """Create an instance of a pull request payload.

        :param title: (required) title of the pull request
        :type title: str
        :param description: human-readable description of the pull request
        :type description: str
        :param reviewers: a set of reviewers for the pull request
        :type reviewers: set(str)
        :param close_source_branch: whether to close the source branch
            when the pull request is merged
        :type close_source_branch: bool
        :param source_repository_full_name: (required) the owner and name
            of the source repository. Like atlassian/pybitbucket
        :type source_repository_full_name: str
        :param source_branch_name: (required) the source branch
            from the source repository.
        :type source_branch_name: str
        :param source_commit: the source commit
            from the source repository.
        :type source_commit: str
        :param destination_branch: the target branch
            in the destination repository.
        :type destination_branch: str
        :param destination_commit: the target commit
            in the destination repository.
        :type destination_commit: str
        :raises: ValueError
        """
        for p in self.properties:
            setattr(self, '_' + p, kwargs.get(p))
        if kwargs.get('source_repository_full_name'):
            owner, name = kwargs['source_repository_full_name'].split('/')
            self._source_repository_owner = owner
            self._source_repository_name = name

    def expect_required(self):
        required = [
            'title',
            'source_branch_name',
            'source_repository_full_name',
            'destination_branch_name']
        for v in required:
            if getattr(self, '_' + v) is None:
                raise KeyError('{0} is required'.format(v))

    @staticmethod
    def update_if_not_none(d, key, value, expression=None):
        expression = expression or value
        if value is not None:
            d.update({key: expression})

    def data(self):
        """Convert this value type to a serializable data structure.

        :returns: dict
        :raises: KeyError
        """
        self.expect_required()
        payload = {
            'title': self._title,
            'source': {
                'branch': {
                    'name': self._source_branch_name
                },
                'repository': {
                    'full_name': self._source_repository_full_name
                }
            },
            'destination': {
                'branch': {
                    'name': self._destination_branch_name
                }
            }
        }
        self.update_if_not_none(
            payload,
            'close_source_branch',
            self._close_source_branch)
        self.update_if_not_none(
            payload,
            'description',
            self._description)
        self.update_if_not_none(
            payload.get('source', {}),
            'commit',
            self._source_commit,
            {'hash': self._source_commit})
        self.update_if_not_none(
            payload.get('destination', {}),
            'commit',
            self._destination_commit,
            {'hash': self._destination_commit})
        if self._reviewers is not None:
            payload.update(
                {'reviewers': [{'username': u} for u in self._reviewers]})

        return payload

    @property
    def title(self):
        return self._title

    @property
    def description(self):
        return self._description

    @property
    def reviewers(self):
        return self._reviewers

    @reviewers.setter
    def reviewers(self, value):
        self.expect_list('reviewers', self._reviewers)
        self._reviewers = value

    @property
    def close_source_branch(self):
        return self._close_source_branch

    @close_source_branch.setter
    def close_source_branch(self, value):
        self.expect_bool('close_source_branch', value)
        self._close_source_branch = value

    @property
    def source_repository_full_name(self):
        return self._source_repository_full_name

    @property
    def source_repository_owner(self):
        return self._source_repository_owner

    @property
    def source_repository_name(self):
        return self._source_repository_name

    @property
    def source_branch_name(self):
        return self._source_branch_name

    @property
    def source_commit(self):
        return self._source_commit

    @property
    def destination_branch_name(self):
        return self._destination_branch_name

    @property
    def destination_commit(self):
        return self._destination_commit


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
        client = client or Client()
        owner = owner or payload.source_repository_owner
        repository_name = repository_name or payload.source_repository_name
        json = payload.data()
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
            PullRequestState.expect_valid_value(state)
        return Bitbucket(client=client).repositoryPullRequestsInState(
            owner=owner,
            repository_name=repository_name,
            state=state)


Client.bitbucket_types.add(PullRequest)
