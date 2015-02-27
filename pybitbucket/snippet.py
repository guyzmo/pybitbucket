import types
from uritemplate import expand

from pybitbucket.bitbucket import Config


class Snippet(object):
    @staticmethod
    def url(username, id):
        template = 'https://{+bitbucket_url}/2.0/snippets/{username}/{id}'
        return expand(template, {'bitbucket_url': Config.bitbucket_url(),
                                 'username': username,
                                 'id': id})

    def __init__(self, client, d):
        self.client = client
        self.__dict__.update(d)
        for link, href in d['links'].iteritems():
            for head, url in href.iteritems():
                # watchers, comments, and commits
                setattr(self, link, types.MethodType(
                    self.client.paginated_get, url))

    def __str__(self):
        "id          : {}\n".format(self.id)
        "is_private  : {}\n".format(self.is_private)
        "is_unlisted : {}\n".format(self.is_unlisted)
        "title       : {}\n".format(self.title)
        "files       : {}\n".format(self.files)
        "creator     : {}\n".format(self.creator)
        "created_on  : {}\n".format(self.created_on)
        "owner       : {}\n".format(self.owner)
        "updated_on  : {}\n".format(self.updated_on)
        "scm         : {}\n".format(self.scm)

    # PUT one
    # {"title": "Updated title"}
    def rename(self, title):
        pass

    # PUT one
    def add(self, files):
        pass

    # DELETE one
    def delete(self):
        url = Snippet.url(self.client.username, self.id)
        r = self.client.session.delete(url)
        # Deletes the snippet and returns 204 (No Content).
        if 204 == r.status_code:
            return
        else:
            raise Exception

    # GET files
    def content(self):
        pass

    # GET one
    def commit(self, sha1):
        pass


class Role(object):
    OWNER = 'owner'
    CONTRIBUTOR = 'contributor'
    MEMBER = 'member'
    roles = [OWNER, CONTRIBUTOR, MEMBER]


# POST
def create_snippet():
    pass


def find_snippets_for_role(client, role=Role.OWNER):
    if role not in Role.roles:
        raise NameError("role '%s' is not in [%s]" %
                        (role, '|'.join(str(x) for x in Role.roles)))
    list_template = 'https://{+bitbucket_url}/2.0/snippets{?role}'
    url = expand(list_template, {'bitbucket_url': Config.bitbucket_url(),
                                 'role': role})
    for snip in client.paginated_get(url):
        yield Snippet(client, snip)


def find_snippet_by_id(client, id):
    url = Snippet.url(client.config.username, id)
    # No! Find may not find anything.
    response = client.session.get(url)
    if 200 == response.status_code:
        return Snippet(client, response.json())
