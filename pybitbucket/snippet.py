import types
from uritemplate import expand

from pybitbucket.bitbucket import BadRequestError
from pybitbucket.bitbucket import Config
from pybitbucket.bitbucket import Client


def open_files(filelist):
    files = {}
    for filename in filelist:
        files.update({'file': open(filename, 'rb')})
    return files


class Snippet(object):
    @staticmethod
    def url(username, id):
        template = 'https://{+bitbucket_url}/2.0/snippets/{username}/{id}'
        return expand(template, {'bitbucket_url': Config.bitbucket_url(),
                                 'username': username,
                                 'id': id})

    @staticmethod
    def make_payload(is_private=None,
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

    def __init__(self, d, client=Client()):
        self.client = client
        self.__dict__.update(d)
        for link, href in d['links'].iteritems():
            for head, url in href.iteritems():
                # watchers, comments, and commits
                setattr(self, link, types.MethodType(
                    self.client.paginated_get, url))
        self.filenames = [str(f) for f in self.files]

    def __unicode__(self):
        return "id:{}".format(self.id)

    def __str__(self):
        return unicode(self).encode('utf-8')

    def modify(self,
               files=open_files([]),
               is_private=None,
               is_unlisted=None,
               title=None):
        url = self.self()
        payload = self.make_payload(is_private, is_unlisted, title)
        response = self.client.session.put(url, data=payload, files=files)
        if 200 == response.status_code:
            return Snippet(response.json(), client=self.client)
        elif 400 == response.status_code:
            raise BadRequestError(response)
        else:
            response.raise_for_status()

    def delete(self):
        url = self.self()
        response = self.client.session.delete(url)
        # Deletes the snippet and returns 204 (No Content).
        if 204 == response.status_code:
            return Snippet(response.json(), client=self.client)
        elif 400 == response.status_code:
            raise BadRequestError(response)
        else:
            response.raise_for_status()

    # GET file
    def content(self, filename):
        pass

    # GET commit
    def commit(self, sha1):
        pass


class Role(object):
    OWNER = 'owner'
    CONTRIBUTOR = 'contributor'
    MEMBER = 'member'
    roles = [OWNER, CONTRIBUTOR, MEMBER]


def create_snippet(files,
                   is_private=None,
                   is_unlisted=None,
                   title=None,
                   scm=None,
                   client=Client()):
    template = 'https://{+bitbucket_url}/2.0/snippets/{username}'
    url = expand(template, {'bitbucket_url': Config.bitbucket_url(),
                            'username': client.config.username})
    payload = Snippet.make_payload(is_private, is_unlisted, title, scm)
    response = client.session.post(url, data=payload, files=files)
    if 200 == response.status_code:
        return Snippet(response.json(), client=client)
    elif 400 == response.status_code:
        raise BadRequestError(response)
    else:
        response.raise_for_status()


def find_snippets_for_role(role=Role.OWNER, client=Client()):
    if role not in Role.roles:
        raise NameError("role '%s' is not in [%s]" %
                        (role, '|'.join(str(x) for x in Role.roles)))
    template = 'https://{+bitbucket_url}/2.0/snippets{?role}'
    url = expand(template, {'bitbucket_url': Config.bitbucket_url(),
                            'role': role})
    for snip in client.paginated_get(url):
        yield Snippet(snip, client=client)


def find_snippet_by_id(id, client=Client()):
    url = Snippet.url(client.config.username, id)
    response = client.session.get(url)
    if 200 == response.status_code:
        return Snippet(response.json(), client=client)
    elif 400 == response.status_code:
        raise BadRequestError(response)
    else:
        response.raise_for_status()
