=============
 PyBitbucket
=============

A Python wrapper for the Bitbucket API.

-----
Using
-----

Override Config
===============

The :code:`Config` class provides credentials.
In the simple case for your own scripts, you can just hardcode credentials:

::

class MyConfig(Config):
    username = 'your_username_here'
    password = 'your_secret_password_here'
    email = 'pybitbucket@mailinator.com'

For a more sophisticated example, see the `implementation from Snippet <https://bitbucket.org/atlassian/snippet/src/master/snippet/config.py>`_.
That implementation reads and writes credentials from a file so command-line users do not have to type them out everytime.
Since your application may have it's own mechanism for configuration, this class lets you wrap whatever you use.

To "plug in" your implementation, just do:

::

Client.configurator = MyConfig
client = Client()

Find Things
===========

For example, to find all your snippets:

::

for snip in Snippet.find_snippets_for_role(client=Client()):
    print(snip)

The method says "for role" but, if not provided, it will use the default of owner.
Hence, all your snippets.

In general, finding things is done with a static find method on each type of resource.
If the resource is plural, like "snippets" above, then the find method is a generator.
You can use it with iterators or comprehensions.
The resources you can find are:

* commit
* repository
* snippet
* team
* user

Create Things
=============

For example, to create a new snippet:

::

snip = Snippet.create_snippet(
    files=open_files(["README.rst"]),
    title="My New Snippet",
    client=Client())

Only snippets can be created.

Examine Things
==============

For example, to examine attributes on a snippet:

::

snip = Snippet.find_snippet_by_id("Xqoz8", Client())
s = '\n'.join([
    "id          : {}".format(snip.id),
    "is_private  : {}".format(snip.is_private),
    "title       : {}".format(snip.title),
    "files       : {}".format(snip.filenames),
    "created_on  : {}".format(snip.created_on),
    "updated_on  : {}".format(snip.updated_on),
    "scm         : {}".format(snip.scm),
    ]) if snip else 'Snippet not found.'
print(s)

What attributes are available?
You will not find them hardcoded in Python.
They are populated dynamically from the JSON response.
You can query the list via a convenience method:

::

snip = Snippet.find_snippet_by_id("Xqoz8", Client())
print(snip.attributes())

Beware. The attributes for the same resource may change depending on how you got to it.

Navigate Relationships
======================

For example, to list the commits for a snippet:

::

snip = Snippet.find_snippet_by_id("Xqoz8", Client())
for commit in snip.commits():
    print(commit)

What relationships are available?
You will not find them hardcoded in Python.
They are populated dynamically from the JSON response.
You can query the list via a convenience method:

::

snip = Snippet.find_snippet_by_id("Xqoz8", Client())
print(snip.relationships())

Just like attributes, the relationships for the same resource may change depending on how you got to it.
If you need the canonical resource with all attributes, use the :code:`self()` relationship:

::

snips = Snippet.find_snippets_for_role(client=Client())
one_snip = next(snips)    # one_snip has no files relationship in this context.
real_snip = next(one_snip.self())
print(real_snip.files)

----------
Developing
----------

Python Virtual Environment Setup (for OS X)
===========================================

It's not virtual like a virtual machine. More like a specialized container for a Python version and libraries.

1. :code:`brew install python` This installs the latest version of Python 2.7 with a version of setuptools and pip. Unfortunately, those versions of setuptools and pip seem to be broken.
2. :code:`pip install --upgrade --no-use-wheel setuptools`
3. :code:`pip install --upgrade --no-use-wheel pip`
4. :code:`pip install virtualenvwrapper`

Project Setup
=============

1. Clone the repository and set it as the current working directory.
2. *(Optional, but good practice)* Create a `virtual environment <http://docs.python-guide.org/en/latest/dev/virtualenvs/>`_: :code:`mkvirtualenv python-bitbucket` Once created, use :code:`workon python-bitbucket` to restore the virtual environment.
3. :code:`pip install -r requirements-dev.txt` Loads required libraries into the virtual environment.
5. :code:`paver test_all` Run all the unit tests and analyze the source code.

----
TODO
----

* :code:`POST` and :code:`DELETE` for :code:`snippet.comments` from `snippets Endpoint <https://confluence.atlassian.com/display/BITBUCKET/snippets+endpoint>`_.
* :code:`PUT` and :code:`DELETE` for :code:`snippet.watch` from `snippets Endpoint <https://confluence.atlassian.com/display/BITBUCKET/snippets+endpoint>`_.
* More version 2 endpoints:
    - branch-restrictions
    - pullrequests
    - pullrequest changesets
* Wrap the `version 1 endpoints <https://confluence.atlassian.com/display/BITBUCKET/Version+1>`_ for:
    - privileges
    - groups
    - group-privileges
    - invitations
* Decide what to do with overlapping endpoints:
    - repositories
    - user
    - users
* Expand possible authentication mechanisms.
* :code:`POST` for :code:`commit` from `REST Browser <http://restbrowser.bitbucket.org/>`_. What does this even mean?
