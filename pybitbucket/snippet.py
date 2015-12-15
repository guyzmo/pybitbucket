"""
Provides classes for manipulating Snippet resources.
"""
from uritemplate import expand

from pybitbucket.bitbucket import Bitbucket, BitbucketBase, Client, enum


def open_files(filelist):
    files = []
    for filename in filelist:
        files.append(('file', (filename, open(filename, 'rb'))))
    return files


SnippetRole = enum(
    'SnippetRole',
    OWNER='owner',
    CONTRIBUTOR='contributor',
    MEMBER='member')


class Snippet(BitbucketBase):
    id_attribute = 'id'

    @staticmethod
    def is_type(data):
        # Snippet URLs look like this:
        # https://api.bitbucket.org/2.0/snippets/pybitbucket/Xqoz8
        # Which doesn't follow the pattern of:
        # resource_type/id_attribute
        # So we can't use `has_v2_self_url` to categorize.
        return (
            # Categorize as 2.0 structure
            (data.get('links') is not None) and
            # It would be nice to categorize as repo-like (repo or snippet).
            # Unfortunately, only the cannonical URL yields the scm attribute.
            # In paged results, the attribute is missing.
            #    (data.get('scm') is not None) and
            # Categorize as snippet, not repo
            (data.get('id') is not None) and
            (data.get('full_name') is None) and
            # Categorize with _type if it is provided.
            # Snippets don't have _type
            (data.get('_type') is None))

    def __init__(self, data, client=Client()):
        super(Snippet, self).__init__(data, client=client)
        if data.get('files'):
            self.filenames = [str(f) for f in data['files']]

    @staticmethod
    def make_payload(
            is_private=None,
            is_unlisted=None,
            title=None,
            scm=None):
        # Since server defaults may change, method defaults are None.
        # If the parameters are not provided, then don't send them
        # so the server can decide what defaults to use.
        payload = {}
        if is_private is not None:
            payload.update({'is_private': is_private})
        if is_unlisted is not None:
            payload.update({'is_unlisted': is_unlisted})
        if title is not None:
            payload.update({'title': title})
        if scm is not None:
            payload.update({'scm': scm})
        return payload

    @staticmethod
    def create_snippet(
            files,
            is_private=None,
            is_unlisted=None,
            title=None,
            scm=None,
            client=Client()):
        template = '{+bitbucket_url}/2.0/snippets/{username}'
        url = expand(
            template, {
                'bitbucket_url': client.get_bitbucket_url(),
                'username': client.get_username()
            })
        payload = Snippet.make_payload(is_private, is_unlisted, title, scm)
        response = client.session.post(url, data=payload, files=files)
        Client.expect_ok(response)
        return Snippet(response.json(), client=client)

    """
    A convenience method for finding snippets by the user's role.
    The method is a generator Snippet objects.
    """
    @staticmethod
    def find_snippets_for_role(role=SnippetRole.OWNER, client=Client()):
        SnippetRole.expect_valid_value(role)
        return Bitbucket(client=client).snippetsForRole(role=role)

    """
    A convenience method for finding a specific snippet.
    In contrast to the pure hypermedia driven method on the Bitbucket
    class, this method returns a Snippet object, instead of the
    generator.
    """
    @staticmethod
    def find_my_snippet_by_id(id, client=Client()):
        return next(Bitbucket(client=client).snippetByOwnerAndSnippetId(
            owner=client.get_username(),
            snippet_id=id))

    """
    A convenience method for finding a specific snippet.
    In contrast to the pure hypermedia driven method on the Bitbucket
    class, this method returns a Snippet object, instead of the
    generator.
    """
    @staticmethod
    def find_snippet_by_owner_and_id(owner, id, client=Client()):
        return next(Bitbucket(client=client).snippetByOwnerAndSnippetId(
            owner=owner,
            snippet_id=id))

    """
    A convenience method for changing the current snippet.
    The parameters make it easier to know what can be changed
    and allow references with file names instead of File objects.
    """
    def modify(
            self,
            files=open_files([]),
            is_private=None,
            is_unlisted=None,
            title=None):
        payload = self.make_payload(is_private, is_unlisted, title)
        return self.put(payload, files=files)

    """
    A convenience method that compensates for a bug in the Bitbucket API.
    """
    def isPrivate(self):
        return (self.data['is_private'] == 'True')

    def content(self, filename):
        if not self.files.get(filename):
            return
        url = self.files[filename]['links']['self']['href']
        response = self.client.session.get(url)
        Client.expect_ok(response)
        return response.content


Client.bitbucket_types.add(Snippet)
