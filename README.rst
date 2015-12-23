=============
 PyBitbucket
=============

A Python wrapper for the Bitbucket Cloud REST API.
This is not known to work with Bitbucket Server,
previously known as Stash.

-----
Using
-----

Authenticate
============

The :code:`Authenticator` subclasses prepare API requests with credentials.
The simplest case is :code:`Anonymous` which connects with no credentials.
:code:`Anonymous` can be used with an publicly available resources.
For private resources,
:code:`BasicAuthenticator` uses email, username, and password as credentials.
If your client application has it's own mechanisms for working with these values,
you can subclass the :code:`BasicAuthenticator` to provide custom behavior.

To "plug in" your implementation or a standard one, just do:

::

    bitbucket = Client(
        BasicAuthenticator(
            'your_username_here',
            'your_secret_password_here',
            'pybitbucket@mailinator.com'))

The :code:`OAuth2Authenticator` is intended as an example and superclass.
It may work for some command-line clients.
Other clients like web applications
will need an appropriate implementation of :code:`obtain_authorization()`
and perhaps may need to use a different grant types.

Find Things
===========

For example, to find all your snippets:

::

    for snip in Snippet.find_snippets_for_role(client=bitbucket):
        print(snip)

The method says "for role" but, if not provided, it will use the default of owner.
Hence, all your snippets.

In general, finding things is done with a static find method on each type of resource.
If the resource is plural, like "snippets" above, then the find method is a generator.
You can use it with iterators or comprehensions.
The resources you can find are:

* user and team
* repository and snippet
* pull request and comment
* commit and build status
* hook and branch restriction

Create Things
=============

For example, to create a new snippet:

::

    snip = Snippet.create_snippet(
        files=open_files(["README.rst"]),
        title="My New Snippet",
        client=bitbucket)

The resources you can create are:

* repository and snippet
* pull request and comment
* build status
* hook and branch restriction

Examine Things
==============

For example, to examine attributes on a snippet:

::

    snip = Snippet.find_snippet_by_id("Xqoz8", bitbucket)
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

    snip = Snippet.find_snippet_by_id("Xqoz8", bitbucket)
    print(snip.attributes())

Beware. The attributes for the same resource may change depending on how you got to it.

Navigate Relationships
======================

For example, to list the commits for a snippet:

::

    snip = Snippet.find_snippet_by_id("Xqoz8", bitbucket)
    for commit in snip.commits():
        print(commit)

What relationships are available?
You will not find them hardcoded in Python.
They are populated dynamically from the JSON response.
You can query the list via a convenience method:

::

    snip = Snippet.find_snippet_by_id("Xqoz8", bitbucket)
    print(snip.relationships())

Just like attributes, the relationships for the same resource may change depending on how you got to it.
If you need the canonical resource with all attributes, use the :code:`self()` relationship:

::

    snips = Snippet.find_snippets_for_role(client=bitbucket)
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
4. :code:`paver test_all` Run all the unit tests and analyze the source code.

Continuous Integration
======================

* `PyBitbucket on Bamboo <https://opensource.atlassian.net/builds/browse/PY-PYBB/>`_
* `PyBitbucket with multiple Docker containers on Bamboo <https://opensource.atlassian.net/builds/browse/PY-PYBBN/>`_

----
TODO
----

* :code:`PUT` and :code:`DELETE` for :code:`snippet.watch` from `snippets Endpoint <https://confluence.atlassian.com/display/BITBUCKET/snippets+endpoint>`_.
* Wrap the `version 1 endpoints <https://confluence.atlassian.com/display/BITBUCKET/Version+1>`_ for:
    - privileges
    - groups
    - group-privileges
    - invitations
* :code:`POST` for :code:`commit` from `REST Browser <http://restbrowser.bitbucket.org/>`_. What does this even mean?
