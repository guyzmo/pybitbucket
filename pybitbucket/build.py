# -*- coding: utf-8 -*-
"""
Provides classes for manipulating Build status resources
on Bitbucket commits.
"""
from uritemplate import expand

from pybitbucket.bitbucket import BitbucketBase, Client


class BuildStatusStates(object):
    INPROGRESS = 'INPROGRESS'
    SUCCESSFUL = 'SUCCESSFUL'
    FAILED = 'FAILED'
    states = [INPROGRESS, SUCCESSFUL, FAILED]


class BuildStatus(BitbucketBase):
    id_attribute = 'name'

    @staticmethod
    def is_type(data):
        return bool(data.get('state'))

    @staticmethod
    def make_payload(
            state=None,
            key=None,
            name=None,
            url=None,
            description=None):
        # Since server defaults may change, method defaults are None.
        # If the parameters are not provided, then don't send them
        # so the server can decide what defaults to use.
        payload = {}
        if state is not None:
            if state not in BuildStatusStates.states:
                raise NameError(
                    "state '%s' is not in [%s]" %
                    (state, '|'.join(
                        str(x) for x in BuildStatusStates.states)))
            payload.update({'state': state})
        if key is not None:
            payload.update({'key': key})
        if name is not None:
            payload.update({'name': name})
        if url is not None:
            payload.update({'url': url})
        if description is not None:
            payload.update({'description': description})
        return payload

    @staticmethod
    def create_buildstatus(
            owner=None,
            repository_name=None,
            revision=None,
            state=None,
            key=None,
            name=None,
            url=None,
            description=None,
            client=Client()):
        template = (
            'https://{+bitbucket_url}' +
            '/2.0/repositories{/owner,repository_name}' +
            '/commit{/revision}/statuses/build')
        # owner, repository_name, and revision are required
        url = expand(
            template, {
                'bitbucket_url': client.get_bitbucket_url(),
                'owner': client.get_username(),
                'repository_name': repository_name,
                'revision': revision
            })
        payload = BuildStatus.make_payload(
            state, key, name, url, description)
        response = client.session.post(url, data=payload)
        Client.expect_ok(response)
        return BuildStatus(response.json(), client=client)

    """
    A convenience method for changing the current build status.
    """
    def modify(self, state=None):
        payload = self.make_payload(
            state,
            self.key,
            self.name,
            self.url,
            self.description)
        return self.put(payload)
