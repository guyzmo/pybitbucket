# -*- coding: utf-8 -*-

from __future__ import unicode_literals

"""
Provides classes for manipulating Snippet resources.

Classes:
- SnippetRole: enumerates the possible roles a user can have with a snippet
- SnippetPayload: encapsulates payload for creating and modifying snippets
- Snippet: represents a snippet
"""

from uritemplate import expand
from voluptuous import Schema, Optional, In

from pybitbucket.bitbucket import (
    Bitbucket, BitbucketBase, Client, PayloadBuilder, RepositoryType, Enum)


def open_files(filelist):
    files = []
    for filename in filelist:
        files.append(('file', (filename, open(filename, 'rb'))))
    return files


class SnippetRole(Enum):
    OWNER = 'owner'
    CONTRIBUTOR = 'contributor'
    MEMBER = 'member'


class SnippetPayload(PayloadBuilder):
    """
    A builder object to help create payloads
    for creating and updating snippets.
    """

    schema = Schema({
        Optional('title'): str,
        Optional('scm'): In(RepositoryType),
        Optional('is_private'): bool
    })

    def __init__(
            self,
            payload=None,
            owner=None):
        super(SnippetPayload, self).__init__(payload=payload)
        self._owner = owner

    @property
    def owner(self):
        return self._owner

    def add_owner(self, owner):
        return SnippetPayload(
            payload=self._payload.copy(),
            owner=owner)

    def add_title(self, title):
        new = self._payload.copy()
        new['title'] = title
        return SnippetPayload(
            payload=new,
            owner=self.owner)

    def add_scm(self, scm):
        new = self._payload.copy()
        new['scm'] = scm
        return SnippetPayload(
            payload=new,
            owner=self.owner)

    def add_is_private(self, is_private):
        new = self._payload.copy()
        new['is_private'] = is_private
        return SnippetPayload(
            payload=new,
            owner=self.owner)


class Snippet(BitbucketBase):
    """Represents a snippet."""

    id_attribute = 'id'
    resource_type = 'snippets'
    templates = {
        'create': '{+bitbucket_url}/2.0/snippets'
    }

    @staticmethod
    def is_type(data):
        # Snippet URLs look like this:
        # https://api.bitbucket.org/2.0/snippets/pybitbucket/Xqoz8
        # Which doesn't follow the pattern of:
        # resource_type/id_attribute
        # So we can't use `has_v2_self_url` to categorize.
        if (
                (data.get('links') is None) or
                (data['links'].get('self') is None) or
                (data['links']['self'].get('href') is None) or
                (data.get(Snippet.id_attribute) is None)):
            return False
        # Since the structure is right, assume it is v2.
        is_v2 = True
        url_path = data['links']['self']['href'].split('/')
        # Start looking from the end of the path.
        position = -1
        is_v2 = is_v2 and (data[Snippet.id_attribute] == url_path[position])
        # After matching the id_attribute,
        # skip a position for the account name.
        # The resource_type should be the preceding part of the path.
        position -= 2
        is_v2 = (Snippet.resource_type == url_path[position])
        return is_v2

    def __init__(self, data, client=Client()):
        super(Snippet, self).__init__(data, client=client)
        if data.get('files'):
            self.filenames = [str(f) for f in data['files']]
        # TODO: Snippet has patch & diff links but I don't know what they do.

    @classmethod
    def create(cls, files, payload=None, client=None):
        """Create a new snippet.

        :param files:
        :type files:
        :param payload: the options for creating the new snippet.
        :type payload: SnippetPayload
        :param client: the configured connection to Bitbucket.
            If not provided, assumes an Anonymous connection.
        :type client: bitbucket.Client
        :returns: the new build status object.
        :rtype: BuildStatus
        :raises: ValueError
        """
        client = client or Client()
        payload = payload or SnippetPayload()
        json = payload.validate().build()
        api_url = expand(
            cls.templates['create'], {
                'bitbucket_url': client.get_bitbucket_url(),
            })
        return cls.post(api_url, json=json, files=files, client=client)

    def modify(self, files=None, payload=None):
        """
        A convenience method for changing the current snippet.
        The parameters make it easier to know what can be changed
        and allow references with file names instead of File objects.
        """
        files = files or open_files([])
        payload = payload or SnippetPayload()
        json = payload.validate().build()
        return self.put(json=json, files=files)

    def content(self, filename):
        """
        A method for obtaining the contents of a file on a snippet.
        If the filename is not on the snippet, no content is returned.
        """
        if not self.files.get(filename):
            return
        url = self.files[filename]['links']['self']['href']
        response = self.client.session.get(url)
        Client.expect_ok(response)
        return response.content

    @staticmethod
    def find_snippets_for_role(role=SnippetRole.OWNER, client=None):
        """
        A convenience method for finding snippets by the user's role.
        The method is a generator Snippet objects.

        :param role: the role of the current user on the snippets.
            If not provided, assumes the relationship owner.
        :type role: SnippetRole
        :param client: the configured connection to Bitbucket.
            If not provided, assumes an Anonymous connection.
        :type client: bitbucket.Client
        :returns: an iterator over the selected snippets.
        :rtype: iterator
        """
        client = client or Client()
        SnippetRole(role)
        return Bitbucket(client=client).snippetsForRole(role=role)

    @staticmethod
    def find_snippet_by_id_and_owner(id, owner=None, client=None):
        """
        A convenience method for finding a specific snippet.
        In contrast to the pure hypermedia driven method on the Bitbucket
        class, this method returns a Snippet object, instead of the
        generator.

        :param id: the id of the snippet.
        :type id: str
        :param owner: the owner of the snippet.
            If not provided, assumes the current user.
        :type owner: str
        :param client: the configured connection to Bitbucket.
            If not provided, assumes an Anonymous connection.
        :type client: bitbucket.Client
        :returns: the snippet referenced by the id.
        :rtype: bitbucket.Snippet
        """
        client = client or Client()
        owner = owner or client.get_username()
        return next(Bitbucket(client=client).snippetByOwnerAndSnippetId(
            owner=owner,
            snippet_id=id))


Client.bitbucket_types.add(Snippet)
