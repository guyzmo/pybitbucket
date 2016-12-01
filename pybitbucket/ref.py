# -*- coding: utf-8 -*-

from __future__ import unicode_literals

"""
Defines the Ref, Tag, and Branch resources
and registers those type with the Client.

Classes:
- Ref: represents the abstraction of a Git reference to a commit
- Tag: represents the tag resource that references a specific commit
- Branch: represents the branch resource that references a set of commits
"""
from pybitbucket.bitbucket import Bitbucket, BitbucketBase, Client


class Ref(BitbucketBase):
    id_attribute = 'name'

    @staticmethod
    def is_type(*args):
        # Ref is an abstraction so does not match on data
        return False

    @staticmethod
    def find_refs_in_repository(
            owner,
            repository_name,
            client=Client()):
        """
        A convenience method for finding refs in a repository.
        The method is a generator Ref subtypes of Tag and Branch.
        """
        return Bitbucket(client=client).repositoryRefs(
            owner=owner,
            repository_name=repository_name)


class Tag(Ref):
    resource_type = 'tags'

    @staticmethod
    def is_type(data):
        return (Tag.has_v2_self_url(data))

    @staticmethod
    def find_tags_in_repository(
            repository_name,
            owner=None,
            client=Client()):
        """
        A convenience method for finding tags in a repository.
        The method is a generator Tag objects.
        """
        owner = owner or client.get_username()
        return Bitbucket(client=client).repositoryTags(
            owner=owner,
            repository_name=repository_name)

    @staticmethod
    def find_tag_by_ref_name_in_repository(
            ref_name,
            repository_name,
            owner=None,
            client=Client()):
        """
        A convenience method for finding a specific tag.
        In contrast to the pure hypermedia driven method on the Bitbucket
        class, this method returns a Tag object, instead of the
        generator.
        """
        owner = owner or client.get_username()
        return next(Bitbucket(client=client).repositoryTagByName(
            owner=owner,
            repository_name=repository_name,
            ref_name=ref_name))


class Branch(Ref):
    resource_type = 'branches'

    @staticmethod
    def is_type(data):
        return (Branch.has_v2_self_url(data))

    @staticmethod
    def find_branches_in_repository(
            repository_name,
            owner=None,
            client=Client()):
        """
        A convenience method for finding branches in a repository.
        The method is a generator Branch objects.
        """
        owner = owner or client.get_username()
        return Bitbucket(client=client).repositoryBranches(
            owner=owner,
            repository_name=repository_name)

    @staticmethod
    def find_branch_by_ref_name_in_repository(
            ref_name,
            repository_name,
            owner=None,
            client=Client()):
        """
        A convenience method for finding a specific branch.
        In contrast to the pure hypermedia driven method on the Bitbucket
        class, this method returns a Branch object, instead of the
        generator.
        """
        owner = owner or client.get_username()
        return next(Bitbucket(client=client).repositoryBranchByName(
            owner=owner,
            repository_name=repository_name,
            ref_name=ref_name))


Client.bitbucket_types.add(Ref)
Client.bitbucket_types.add(Tag)
Client.bitbucket_types.add(Branch)
