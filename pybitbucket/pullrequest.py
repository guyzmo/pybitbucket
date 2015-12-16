"""
Provides a class for manipulating PullRequest resources on Bitbucket.
"""
import json
from uritemplate import expand

from pybitbucket.bitbucket import Bitbucket, BitbucketBase, Client


class PullRequestState(object):
    OPEN = 'open'
    MERGED = 'merged'
    DECLINED = 'declined'
    states = [OPEN, MERGED, DECLINED]

    @staticmethod
    def expect_state(s):
        if s not in PullRequestState.states:
            raise NameError(
                "state '{}' is not in [{}]".format(
                    s,
                    '|'.join(str(x) for x in PullRequestState.states)))


class PullRequest(BitbucketBase):
    id_attribute = 'id'

    @staticmethod
    def is_type(data):
        return (
            # Categorize as 2.0 structure
            (data.get('links') is not None) and
            # Categorize as not repo-like (repo or snippet)
            (data.get('scm') is None) and
            # Categorize as pullrequest with source and destination
            (data.get('source') is not None) and
            (data.get('destination') is not None))

    def __init__(self, data, client=Client()):
        super(PullRequest, self).__init__(data, client=client)
        if data.get('author'):
            self.author = client.convert_to_object(data['author'])
        if data.get('reviewers'):
            self.reviewers = [
                client.convert_to_object(x)
                for x
                in data['reviewers']]
        if data.get('source'):
            if data['source'].get('commit'):
                self.source_commit = client.convert_to_object(
                    data['source']['commit'])
            if data['source'].get('repository'):
                self.source_repository = client.convert_to_object(
                    data['source']['repository'])
        if data.get('destination'):
            if data['destination'].get('commit'):
                self.destination_commit = client.convert_to_object(
                    data['destination']['commit'])
            if data['destination'].get('repository'):
                self.destination_repository = client.convert_to_object(
                    data['destination']['repository'])

    # TODO: Push up to BitbucketBase, refactor Repository
    @staticmethod
    def expect_bool(name, value):
        if not isinstance(value, bool):
            raise NameError(
                "{} is {} instead of bool".format(name, type(value)))

    @staticmethod
    def make_new_pullrequest_payload(
            title,
            source_branch_name,
            source_repository_full_name,
            destination_branch_name,
            close_source_branch=None,
            description=None,
            reviewers=None):
        payload = {
            'title': title,
            'source': {
                'branch': {
                    'name': source_branch_name
                },
                'repository': {
                    'full_name': source_repository_full_name
                }
            },
            'destination': {
                'branch': {
                    'name': destination_branch_name
                }
            }
        }
        # Since server defaults may change, method defaults are None.
        # If the parameters are not provided, then don't send them
        # so the server can decide what defaults to use.
        if close_source_branch is not None:
            PullRequest.expect_bool('close_source_branch', close_source_branch)
            payload.update({'close_source_branch': close_source_branch})
        if description is not None:
            payload.update({'description': description})
        if reviewers is not None:
            [payload.update({'username': u}) for u in reviewers]
        return payload

    @staticmethod
    def create_pullrequest(
            username,
            repository_name,
            title,
            source_branch_name,
            destination_branch_name,
            close_source_branch=None,
            description=None,
            reviewers=None,
            client=Client()):
        template = (
            '{+bitbucket_url}' +
            '/2.0/repositories{/username,repository_name}/pullrequests')
        url = expand(
            template,
            {
                'bitbucket_url': client.get_bitbucket_url(),
                'username': username,
                'repository_name': repository_name
            })
        payload = PullRequest.make_new_pullrequest_payload(
            title,
            source_branch_name,
            (username + '/' + repository_name),
            destination_branch_name,
            close_source_branch,
            description,
            reviewers)
        return PullRequest.post(url, data=payload)

    """
    A convenience method for finding a specific pull request.
    In contrast to the pure hypermedia driven method on the Bitbucket
    class, this method returns a PullRequest object, instead of the
    generator.
    """
    @staticmethod
    def find_pullrequest_in_repository_by_id(
            owner,
            repository_name,
            pullrequest_id,
            client=Client()):
        return next(
            Bitbucket(client=client).repositoryPullRequestByPullRequestId(
                owner=owner,
                repository_name=repository_name,
                pullrequest_id=pullrequest_id))

    """
    A convenience method for finding pull requests for a repository.
    The method is a generator PullRequest objects.
    If no owner is provided, this method assumes the client can provide one.
    If no state is provided, the server will assume open pull requests.
    """
    @staticmethod
    def find_pullrequests_for_repository_by_state(
            repository_name,
            owner=None,
            state=None,
            client=Client()):
        if (state is not None):
            PullRequestState.expect_state(state)
        if (owner is None):
            owner = client.get_username()
        return Bitbucket(client=client).repositoryPullRequestsInState(
            owner=owner,
            repository_name=repository_name,
            state=state)


Client.bitbucket_types.add(PullRequest)
