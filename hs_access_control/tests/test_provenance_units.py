__author__ = 'Alva'

import unittest
from django.http import Http404
from django.test import TestCase
from django.utils import timezone
from django.core.exceptions import PermissionDenied
from django.contrib.auth.models import User, Group
from pprint import pprint

from hs_access_control.models import UserAccess, GroupAccess, ResourceAccess, \
    UserResourceProvenance, UserResourcePrivilege, \
    GroupResourceProvenance, GroupResourcePrivilege, \
    UserGroupProvenance, UserGroupPrivilege, \
    PrivilegeCodes

from hs_core import hydroshare
from hs_core.models import GenericResource, BaseResource
from hs_core.testing import MockIRODSTestCaseMixin

from hs_access_control.tests.utilities import *


class UnitTests(MockIRODSTestCaseMixin, TestCase):
    """ test basic behavior of each routine """

    def setUp(self):
        super(UnitTests, self).setUp()
        global_reset()
        self.group, _ = Group.objects.get_or_create(name='Hydroshare Author')

        self.alva = hydroshare.create_account(
            'alva@gmail.com',
            username='alva',
            first_name='alva',
            last_name='couch',
            superuser=False,
            groups=[]
        )

        self.george = hydroshare.create_account(
            'george@gmail.com',
            username='george',
            first_name='george',
            last_name='miller',
            superuser=False,
            groups=[]
        )

        self.john = hydroshare.create_account(
            'john@gmail.com',
            username='john',
            first_name='john',
            last_name='miller',
            superuser=False,
            groups=[]
        )

        self.admin = hydroshare.create_account(
            'admin@gmail.com',
            username='admin',
            first_name='first_name_admin',
            last_name='last_name_admin',
            superuser=True,
            groups=[]
        )

        # george creates a entity 'bikes'
        self.bikes = hydroshare.create_resource(
            resource_type='GenericResource',
            owner=self.george,
            title='Bikes',
            metadata=[],
        )

        # george creates a entity 'bikers'
        self.bikers = self.george.uaccess.create_group('Bikers', 'Of the human powered kind')

    def test_usergroupprivilege_get_current_record(self):
        george = self.george
        bikers = self.bikers
        alva = self.alva
        UserGroupProvenance.update(
            group=bikers,
            user=alva,
            privilege=PrivilegeCodes.CHANGE,
            grantor=george)
        record = UserGroupProvenance.get_current_record(
            group=bikers, user=alva)
        self.assertEqual(record.grantor, george)
        self.assertEqual(record.group, bikers)
        self.assertEqual(record.user, alva)

    def test_usergroupprivilege_get_undo_users(self):
        george = self.george
        bikers = self.bikers
        alva = self.alva
        UserGroupProvenance.update(
            group=bikers,
            user=alva,
            privilege=PrivilegeCodes.CHANGE,
            grantor=george)
        self.assertTrue(
            is_equal_to_as_set(
                UserGroupProvenance.get_undo_users(
                    group=bikers,
                    grantor=george),
                [alva]))

    def test_usergroupprivilege_get_privilege(self):
        george = self.george
        bikers = self.bikers
        alva = self.alva
        self.assertEqual(
            UserGroupProvenance.get_privilege(
                group=bikers,
                user=alva),
            PrivilegeCodes.NONE)
        UserGroupProvenance.update(
            group=bikers,
            user=alva,
            privilege=PrivilegeCodes.CHANGE,
            grantor=george)
        self.assertEqual(
            UserGroupProvenance.get_privilege(
                group=bikers,
                user=alva),
            PrivilegeCodes.CHANGE)

    def test_usergroupprivilege_update(self):
        george = self.george
        bikers = self.bikers
        alva = self.alva
        self.assertEqual(
            UserGroupProvenance.get_privilege(
                group=bikers,
                user=alva),
            PrivilegeCodes.NONE)
        UserGroupProvenance.update(
            group=bikers,
            user=alva,
            privilege=PrivilegeCodes.CHANGE,
            grantor=george)
        self.assertEqual(
            UserGroupProvenance.get_privilege(
                group=bikers,
                user=alva),
            PrivilegeCodes.CHANGE)

    def test_usergroupprivilege_undo_share(self):
        george = self.george
        bikers = self.bikers
        alva = self.alva
        self.assertEqual(
            UserGroupProvenance.get_privilege(
                group=bikers,
                user=alva),
            PrivilegeCodes.NONE)
        UserGroupProvenance.update(
            group=bikers,
            user=alva,
            privilege=PrivilegeCodes.CHANGE,
            grantor=george)
        self.assertEqual(
            UserGroupProvenance.get_privilege(
                group=bikers,
                user=alva),
            PrivilegeCodes.CHANGE)
        UserGroupProvenance.update(
            group=bikers,
            user=alva,
            privilege=PrivilegeCodes.NONE,
            grantor=george)
        self.assertEqual(
            UserGroupProvenance.get_privilege(
                group=bikers,
                user=alva),
            PrivilegeCodes.NONE)
        UserGroupProvenance.update(
            group=bikers,
            user=alva,
            privilege=PrivilegeCodes.VIEW,
            grantor=george)
        self.assertEqual(
            UserGroupProvenance.get_privilege(
                group=bikers,
                user=alva),
            PrivilegeCodes.VIEW)
        UserGroupProvenance.undo_share(group=bikers, user=alva, grantor=george)
        self.assertEqual(
            UserGroupProvenance.get_privilege(
                group=bikers,
                user=alva),
            PrivilegeCodes.NONE)
        UserGroupProvenance.undo_share(group=bikers, user=alva, grantor=george)
        self.assertEqual(
            UserGroupProvenance.get_privilege(
                group=bikers,
                user=alva),
            PrivilegeCodes.CHANGE)
        UserGroupProvenance.undo_share(group=bikers, user=alva, grantor=george)
        self.assertEqual(
            UserGroupProvenance.get_privilege(
                group=bikers,
                user=alva),
            PrivilegeCodes.NONE)
        UserGroupProvenance.update(
            group=bikers,
            user=alva,
            privilege=PrivilegeCodes.VIEW,
            grantor=george)
        self.assertEqual(
            UserGroupProvenance.get_privilege(
                group=bikers,
                user=alva),
            PrivilegeCodes.VIEW)
        UserGroupProvenance.update(
            group=bikers,
            user=alva,
            privilege=PrivilegeCodes.CHANGE,
            grantor=george)
        self.assertEqual(
            UserGroupProvenance.get_privilege(
                group=bikers,
                user=alva),
            PrivilegeCodes.CHANGE)
        UserGroupProvenance.undo_share(group=bikers, user=alva, grantor=george)
        self.assertEqual(
            UserGroupProvenance.get_privilege(
                group=bikers,
                user=alva),
            PrivilegeCodes.VIEW)
        UserGroupProvenance.update(
            group=bikers,
            user=alva,
            privilege=PrivilegeCodes.NONE,
            grantor=george)
        self.assertEqual(
            UserGroupProvenance.get_privilege(
                group=bikers,
                user=alva),
            PrivilegeCodes.NONE)
        UserGroupProvenance.update(
            group=bikers,
            user=alva,
            privilege=PrivilegeCodes.CHANGE,
            grantor=george)
        self.assertEqual(
            UserGroupProvenance.get_privilege(
                group=bikers,
                user=alva),
            PrivilegeCodes.CHANGE)
        # print("STATE OF UserGroupProvenance:")
        # for p in UserGroupProvenance.objects.all().order_by('start'): print(p)

    def test_usergroupresult_get_privilege(self):
        george = self.george
        bikers = self.bikers
        alva = self.alva
        self.assertEqual(
            UserGroupPrivilege.get_privilege(
                group=bikers,
                user=alva),
            PrivilegeCodes.NONE)
        UserGroupPrivilege.update(
            group=bikers,
            user=alva,
            privilege=PrivilegeCodes.CHANGE,
            grantor=george)
        self.assertEqual(
            UserGroupPrivilege.get_privilege(
                group=bikers,
                user=alva),
            PrivilegeCodes.CHANGE)

    def test_usergroupresult_update(self):
        george = self.george
        bikers = self.bikers
        alva = self.alva
        self.assertEqual(
            UserGroupPrivilege.get_privilege(
                group=bikers,
                user=alva),
            PrivilegeCodes.NONE)
        UserGroupPrivilege.update(
            group=bikers,
            user=alva,
            privilege=PrivilegeCodes.CHANGE,
            grantor=george)
        self.assertEqual(
            UserGroupPrivilege.get_privilege(
                group=bikers,
                user=alva),
            PrivilegeCodes.CHANGE)

    def test_userresourceprivilege_get_current_record(self):
        george = self.george
        bikes = self.bikes
        alva = self.alva
        UserResourceProvenance.update(
            resource=bikes,
            user=alva,
            privilege=PrivilegeCodes.CHANGE,
            grantor=george)
        record = UserResourceProvenance.get_current_record(
            resource=bikes, user=alva)
        self.assertEqual(record.grantor, george)
        self.assertEqual(record.resource, bikes)
        self.assertEqual(record.user, alva)

    def test_userresourceprivilege_get_undo_users(self):
        george = self.george
        bikes = self.bikes
        alva = self.alva
        UserResourceProvenance.update(
            resource=bikes,
            user=alva,
            privilege=PrivilegeCodes.CHANGE,
            grantor=george)
        pprint(
            UserResourceProvenance.get_undo_users(
                resource=bikes,
                grantor=george))
        self.assertTrue(
            is_equal_to_as_set(
                UserResourceProvenance.get_undo_users(
                    resource=bikes,
                    grantor=george),
                [alva]))

    def test_userresourceprivilege_get_privilege(self):
        george = self.george
        bikes = self.bikes
        alva = self.alva
        self.assertEqual(
            UserResourceProvenance.get_privilege(
                resource=bikes,
                user=alva),
            PrivilegeCodes.NONE)
        UserResourceProvenance.update(
            resource=bikes,
            user=alva,
            privilege=PrivilegeCodes.CHANGE,
            grantor=george)
        self.assertEqual(
            UserResourceProvenance.get_privilege(
                resource=bikes,
                user=alva),
            PrivilegeCodes.CHANGE)

    def test_userresourceprivilege_update(self):
        george = self.george
        bikes = self.bikes
        alva = self.alva
        self.assertEqual(
            UserResourceProvenance.get_privilege(
                resource=bikes,
                user=alva),
            PrivilegeCodes.NONE)
        UserResourceProvenance.update(
            resource=bikes,
            user=alva,
            privilege=PrivilegeCodes.CHANGE,
            grantor=george)
        self.assertEqual(
            UserResourceProvenance.get_privilege(
                resource=bikes,
                user=alva),
            PrivilegeCodes.CHANGE)

    def test_userresourceprivilege_undo_share(self):
        george = self.george
        bikes = self.bikes
        alva = self.alva
        self.assertEqual(
            UserResourceProvenance.get_privilege(
                resource=bikes,
                user=alva),
            PrivilegeCodes.NONE)
        UserResourceProvenance.update(
            resource=bikes,
            user=alva,
            privilege=PrivilegeCodes.CHANGE,
            grantor=george)
        self.assertEqual(
            UserResourceProvenance.get_privilege(
                resource=bikes,
                user=alva),
            PrivilegeCodes.CHANGE)
        UserResourceProvenance.update(
            resource=bikes,
            user=alva,
            privilege=PrivilegeCodes.NONE,
            grantor=george)
        self.assertEqual(
            UserResourceProvenance.get_privilege(
                resource=bikes,
                user=alva),
            PrivilegeCodes.NONE)
        UserResourceProvenance.update(
            resource=bikes,
            user=alva,
            privilege=PrivilegeCodes.VIEW,
            grantor=george)
        self.assertEqual(
            UserResourceProvenance.get_privilege(
                resource=bikes,
                user=alva),
            PrivilegeCodes.VIEW)
        UserResourceProvenance.undo_share(resource=bikes, user=alva, grantor=george)
        self.assertEqual(
            UserResourceProvenance.get_privilege(
                resource=bikes,
                user=alva),
            PrivilegeCodes.NONE)
        UserResourceProvenance.undo_share(resource=bikes, user=alva, grantor=george)
        self.assertEqual(
            UserResourceProvenance.get_privilege(
                resource=bikes,
                user=alva),
            PrivilegeCodes.CHANGE)
        UserResourceProvenance.undo_share(resource=bikes, user=alva, grantor=george)
        self.assertEqual(
            UserResourceProvenance.get_privilege(
                resource=bikes,
                user=alva),
            PrivilegeCodes.NONE)
        UserResourceProvenance.update(
            resource=bikes,
            user=alva,
            privilege=PrivilegeCodes.VIEW,
            grantor=george)
        self.assertEqual(
            UserResourceProvenance.get_privilege(
                resource=bikes,
                user=alva),
            PrivilegeCodes.VIEW)
        UserResourceProvenance.update(
            resource=bikes,
            user=alva,
            privilege=PrivilegeCodes.CHANGE,
            grantor=george)
        self.assertEqual(
            UserResourceProvenance.get_privilege(
                resource=bikes,
                user=alva),
            PrivilegeCodes.CHANGE)
        UserResourceProvenance.undo_share(resource=bikes, user=alva, grantor=george)
        self.assertEqual(
            UserResourceProvenance.get_privilege(
                resource=bikes,
                user=alva),
            PrivilegeCodes.VIEW)
        UserResourceProvenance.update(
            resource=bikes,
            user=alva,
            privilege=PrivilegeCodes.NONE,
            grantor=george)
        self.assertEqual(
            UserResourceProvenance.get_privilege(
                resource=bikes,
                user=alva),
            PrivilegeCodes.NONE)
        UserResourceProvenance.update(
            resource=bikes,
            user=alva,
            privilege=PrivilegeCodes.CHANGE,
            grantor=george)
        self.assertEqual(
            UserResourceProvenance.get_privilege(
                resource=bikes,
                user=alva),
            PrivilegeCodes.CHANGE)

    def test_userresourceresult_get_privilege(self):
        george = self.george
        bikes = self.bikes
        alva = self.alva
        self.assertEqual(
            UserResourceProvenance.get_privilege(
                resource=bikes,
                user=alva),
            PrivilegeCodes.NONE)
        UserResourcePrivilege.update(
            resource=bikes,
            user=alva,
            privilege=PrivilegeCodes.CHANGE,
            grantor=george)
        self.assertEqual(
            UserResourcePrivilege.get_privilege(
                resource=bikes,
                user=alva),
            PrivilegeCodes.CHANGE)

    def test_userresourceresult_update(self):
        george = self.george
        bikes = self.bikes
        alva = self.alva
        self.assertEqual(
            UserResourcePrivilege.get_privilege(
                resource=bikes,
                user=alva),
            PrivilegeCodes.NONE)
        UserResourcePrivilege.update(
            resource=bikes,
            user=alva,
            privilege=PrivilegeCodes.CHANGE,
            grantor=george)
        self.assertEqual(
            UserResourcePrivilege.get_privilege(
                resource=bikes,
                user=alva),
            PrivilegeCodes.CHANGE)

    def test_groupresourceprivilege_get_current_record(self):
        george = self.george
        bikes = self.bikes
        bikers = self.bikers
        GroupResourceProvenance.update(
            resource=bikes,
            group=bikers,
            privilege=PrivilegeCodes.CHANGE,
            grantor=george)
        record = GroupResourceProvenance.get_current_record(
            resource=bikes, group=bikers)
        self.assertEqual(record.grantor, george)
        self.assertEqual(record.resource, bikes)
        self.assertEqual(record.group, bikers)

    def test_groupresourceprivilege_get_undo_groups(self):
        george = self.george
        bikes = self.bikes
        bikers = self.bikers
        GroupResourceProvenance.update(
            resource=bikes,
            group=bikers,
            privilege=PrivilegeCodes.CHANGE,
            grantor=george)
        self.assertTrue(
            is_equal_to_as_set(
                GroupResourceProvenance.get_undo_groups(
                    resource=bikes,
                    grantor=george),
                [bikers]))

    def test_groupresourceprivilege_update(self):
        george = self.george
        bikes = self.bikes
        bikers = self.bikers
        self.assertEqual(
            GroupResourceProvenance.get_privilege(
                resource=bikes,
                group=bikers),
            PrivilegeCodes.NONE)
        GroupResourceProvenance.update(
            resource=bikes,
            group=bikers,
            privilege=PrivilegeCodes.CHANGE,
            grantor=george)
        self.assertEqual(
            GroupResourceProvenance.get_privilege(
                resource=bikes,
                group=bikers),
            PrivilegeCodes.CHANGE)

    def test_groupresourceprivilege_get_privilege(self):
        george = self.george
        bikes = self.bikes
        bikers = self.bikers
        self.assertEqual(
            GroupResourceProvenance.get_privilege(
                resource=bikes,
                group=bikers),
            PrivilegeCodes.NONE)
        GroupResourceProvenance.update(
            resource=bikes,
            group=bikers,
            privilege=PrivilegeCodes.CHANGE,
            grantor=george)
        self.assertEqual(
            GroupResourceProvenance.get_privilege(
                resource=bikes,
                group=bikers),
            PrivilegeCodes.CHANGE)

    def test_groupresourceprivilege_undo_share(self):
        george = self.george
        bikes = self.bikes
        bikers = self.bikers
        self.assertEqual(
            GroupResourceProvenance.get_privilege(
                resource=bikes,
                group=bikers),
            PrivilegeCodes.NONE)
        GroupResourceProvenance.update(
            resource=bikes,
            group=bikers,
            privilege=PrivilegeCodes.CHANGE,
            grantor=george)
        self.assertEqual(
            GroupResourceProvenance.get_privilege(
                resource=bikes,
                group=bikers),
            PrivilegeCodes.CHANGE)
        GroupResourceProvenance.update(
            resource=bikes,
            group=bikers,
            privilege=PrivilegeCodes.NONE,
            grantor=george)
        self.assertEqual(
            GroupResourceProvenance.get_privilege(
                resource=bikes,
                group=bikers),
            PrivilegeCodes.NONE)
        GroupResourceProvenance.update(
            resource=bikes,
            group=bikers,
            privilege=PrivilegeCodes.VIEW,
            grantor=george)
        self.assertEqual(
            GroupResourceProvenance.get_privilege(
                resource=bikes,
                group=bikers),
            PrivilegeCodes.VIEW)
        GroupResourceProvenance.undo_share(resource=bikes, group=bikers, grantor=george)
        self.assertEqual(
            GroupResourceProvenance.get_privilege(
                resource=bikes,
                group=bikers),
            PrivilegeCodes.NONE)
        GroupResourceProvenance.undo_share(resource=bikes, group=bikers, grantor=george)
        self.assertEqual(
            GroupResourceProvenance.get_privilege(
                resource=bikes,
                group=bikers),
            PrivilegeCodes.CHANGE)
        GroupResourceProvenance.undo_share(resource=bikes, group=bikers, grantor=george)
        self.assertEqual(
            GroupResourceProvenance.get_privilege(
                resource=bikes,
                group=bikers),
            PrivilegeCodes.NONE)
        GroupResourceProvenance.update(
            resource=bikes,
            group=bikers,
            privilege=PrivilegeCodes.VIEW,
            grantor=george)
        self.assertEqual(
            GroupResourceProvenance.get_privilege(
                resource=bikes,
                group=bikers),
            PrivilegeCodes.VIEW)
        GroupResourceProvenance.update(
            resource=bikes,
            group=bikers,
            privilege=PrivilegeCodes.CHANGE,
            grantor=george)
        self.assertEqual(
            GroupResourceProvenance.get_privilege(
                resource=bikes,
                group=bikers),
            PrivilegeCodes.CHANGE)
        GroupResourceProvenance.undo_share(resource=bikes, group=bikers, grantor=george)
        self.assertEqual(
            GroupResourceProvenance.get_privilege(
                resource=bikes,
                group=bikers),
            PrivilegeCodes.VIEW)
        GroupResourceProvenance.update(
            resource=bikes,
            group=bikers,
            privilege=PrivilegeCodes.NONE,
            grantor=george)
        self.assertEqual(
            GroupResourceProvenance.get_privilege(
                resource=bikes,
                group=bikers),
            PrivilegeCodes.NONE)
        GroupResourceProvenance.update(
            resource=bikes,
            group=bikers,
            privilege=PrivilegeCodes.CHANGE,
            grantor=george)
        self.assertEqual(
            GroupResourceProvenance.get_privilege(
                resource=bikes,
                group=bikers),
            PrivilegeCodes.CHANGE)

    def test_groupresourceresult_update(self):
        george = self.george
        bikes = self.bikes
        bikers = self.bikers
        self.assertEqual(
            GroupResourcePrivilege.get_privilege(
                resource=bikes,
                group=bikers),
            PrivilegeCodes.NONE)
        GroupResourcePrivilege.update(
            resource=bikes,
            group=bikers,
            privilege=PrivilegeCodes.CHANGE,
            grantor=george)
        self.assertEqual(
            GroupResourcePrivilege.get_privilege(
                resource=bikes,
                group=bikers),
            PrivilegeCodes.CHANGE)

    def test_groupresourceresult_get_privilege(self):
        george = self.george
        bikes = self.bikes
        bikers = self.bikers
        self.assertEqual(
            GroupResourcePrivilege.get_privilege(
                resource=bikes,
                group=bikers),
            PrivilegeCodes.NONE)
        GroupResourcePrivilege.update(
            resource=bikes,
            group=bikers,
            privilege=PrivilegeCodes.CHANGE,
            grantor=george)
        self.assertEqual(
            GroupResourcePrivilege.get_privilege(
                resource=bikes,
                group=bikers),
            PrivilegeCodes.CHANGE)

    def test_get_group_undo_users(self):
        george = self.george
        bikers = self.bikers
        alva = self.alva
        self.assertTrue(is_equal_to_as_set(george.uaccess.get_group_undo_users(bikers), []))
        self.assertTrue(is_equal_to_as_set(alva.uaccess.get_group_undo_users(bikers), []))
        self.assertEqual(
            UserGroupPrivilege.get_privilege(
                group=bikers,
                user=alva),
            PrivilegeCodes.NONE)
        george.uaccess.share_group_with_user(bikers, alva, PrivilegeCodes.CHANGE)
        self.assertEqual(
            UserGroupPrivilege.get_privilege(
                group=bikers,
                user=alva),
            PrivilegeCodes.CHANGE)
        self.assertTrue(is_equal_to_as_set(george.uaccess.get_group_undo_users(bikers), [alva]))
        self.assertTrue(is_equal_to_as_set(alva.uaccess.get_group_undo_users(bikers), []))
        george.uaccess.undo_share_group_with_user(bikers, alva)
        self.assertEqual(
            UserGroupPrivilege.get_privilege(group=bikers, user=alva),
            PrivilegeCodes.NONE)
        self.assertTrue(is_equal_to_as_set(george.uaccess.get_group_undo_users(bikers), []))
        self.assertTrue(is_equal_to_as_set(alva.uaccess.get_group_undo_users(bikers), []))
        george.uaccess.share_group_with_user(bikers, alva, PrivilegeCodes.VIEW)
        self.assertEqual(
            UserGroupPrivilege.get_privilege(group=bikers, user=alva),
            PrivilegeCodes.VIEW)
        self.assertTrue(is_equal_to_as_set(george.uaccess.get_group_undo_users(bikers), [alva]))
        self.assertTrue(is_equal_to_as_set(alva.uaccess.get_group_undo_users(bikers), []))
        george.uaccess.undo_share_group_with_user(bikers, alva)
        self.assertEqual(
            UserGroupPrivilege.get_privilege(group=bikers, user=alva),
            PrivilegeCodes.NONE)
        self.assertTrue(is_equal_to_as_set(george.uaccess.get_group_undo_users(bikers), []))
        self.assertTrue(is_equal_to_as_set(alva.uaccess.get_group_undo_users(bikers), []))

    def test_can_undo_share_group_with_user(self):
        george = self.george
        bikers = self.bikers
        alva = self.alva
        self.assertFalse(george.uaccess.can_undo_share_group_with_user(bikers, alva))
        self.assertFalse(george.uaccess.can_undo_share_group_with_user(bikers, george))
        self.assertFalse(alva.uaccess.can_undo_share_group_with_user(bikers, george))
        self.assertEqual(
            UserGroupPrivilege.get_privilege(group=bikers, user=alva),
            PrivilegeCodes.NONE)
        george.uaccess.share_group_with_user(bikers, alva, PrivilegeCodes.CHANGE)
        self.assertEqual(
            UserGroupPrivilege.get_privilege(group=bikers, user=alva),
            PrivilegeCodes.CHANGE)
        self.assertTrue(george.uaccess.can_undo_share_group_with_user(bikers, alva))
        self.assertFalse(george.uaccess.can_undo_share_group_with_user(bikers, george))
        self.assertFalse(alva.uaccess.can_undo_share_group_with_user(bikers, george))
        george.uaccess.undo_share_group_with_user(bikers, alva)
        print("privilege is " + str(UserGroupPrivilege.get_privilege(group=bikers, user=alva)))

        self.assertEqual(
            UserGroupPrivilege.get_privilege(group=bikers, user=alva),
            PrivilegeCodes.NONE)
        self.assertFalse(george.uaccess.can_undo_share_group_with_user(bikers, alva))
        self.assertFalse(george.uaccess.can_undo_share_group_with_user(bikers, george))
        self.assertFalse(alva.uaccess.can_undo_share_group_with_user(bikers, george))
        george.uaccess.share_group_with_user(bikers, alva, PrivilegeCodes.VIEW)
        self.assertEqual(
            UserGroupPrivilege.get_privilege(group=bikers, user=alva),
            PrivilegeCodes.VIEW)
        self.assertTrue(george.uaccess.can_undo_share_group_with_user(bikers, alva))
        self.assertFalse(george.uaccess.can_undo_share_group_with_user(bikers, george))
        self.assertFalse(alva.uaccess.can_undo_share_group_with_user(bikers, george))
        george.uaccess.undo_share_group_with_user(bikers, alva)
        self.assertEqual(
            UserGroupPrivilege.get_privilege(group=bikers, user=alva),
            PrivilegeCodes.NONE)
        self.assertFalse(george.uaccess.can_undo_share_group_with_user(bikers, alva))
        self.assertFalse(george.uaccess.can_undo_share_group_with_user(bikers, george))
        self.assertFalse(alva.uaccess.can_undo_share_group_with_user(bikers, george))

    def test_undo_share_group_with_user(self):
        george = self.george
        bikers = self.bikers
        alva = self.alva
        self.assertEqual(
            UserGroupPrivilege.get_privilege(group=bikers, user=alva),
            PrivilegeCodes.NONE)
        george.uaccess.share_group_with_user(bikers, alva, PrivilegeCodes.CHANGE)
        self.assertEqual(
            UserGroupPrivilege.get_privilege(group=bikers, user=alva),
            PrivilegeCodes.CHANGE)
        george.uaccess.undo_share_group_with_user(bikers, alva)
        self.assertEqual(
            UserGroupPrivilege.get_privilege(group=bikers, user=alva),
            PrivilegeCodes.NONE)
        george.uaccess.share_group_with_user(bikers, alva, PrivilegeCodes.VIEW)
        self.assertEqual(
            UserGroupPrivilege.get_privilege(group=bikers, user=alva),
            PrivilegeCodes.VIEW)
        george.uaccess.undo_share_group_with_user(bikers, alva)
        self.assertEqual(
            UserGroupPrivilege.get_privilege(group=bikers, user=alva),
            PrivilegeCodes.NONE)

    def test_get_resource_undo_users(self):
        george = self.george
        bikes = self.bikes
        alva = self.alva
        self.assertTrue(is_equal_to_as_set(george.uaccess.get_resource_undo_users(bikes), []))
        self.assertTrue(is_equal_to_as_set(alva.uaccess.get_resource_undo_users(bikes), []))
        self.assertEqual(
            UserResourcePrivilege.get_privilege(
                resource=bikes,
                user=alva),
            PrivilegeCodes.NONE)
        george.uaccess.share_resource_with_user(bikes, alva, PrivilegeCodes.CHANGE)
        self.assertEqual(
            UserResourcePrivilege.get_privilege(
                resource=bikes,
                user=alva),
            PrivilegeCodes.CHANGE)
        self.assertTrue(is_equal_to_as_set(george.uaccess.get_resource_undo_users(bikes), [alva]))
        self.assertTrue(is_equal_to_as_set(alva.uaccess.get_resource_undo_users(bikes), []))
        george.uaccess.undo_share_resource_with_user(bikes, alva)
        self.assertEqual(
            UserResourcePrivilege.get_privilege(resource=bikes, user=alva),
            PrivilegeCodes.NONE)
        self.assertTrue(is_equal_to_as_set(george.uaccess.get_resource_undo_users(bikes), []))
        self.assertTrue(is_equal_to_as_set(alva.uaccess.get_resource_undo_users(bikes), []))
        george.uaccess.share_resource_with_user(bikes, alva, PrivilegeCodes.VIEW)
        self.assertEqual(
            UserResourcePrivilege.get_privilege(resource=bikes, user=alva),
            PrivilegeCodes.VIEW)
        self.assertTrue(is_equal_to_as_set(george.uaccess.get_resource_undo_users(bikes), [alva]))
        self.assertTrue(is_equal_to_as_set(alva.uaccess.get_resource_undo_users(bikes), []))
        george.uaccess.undo_share_resource_with_user(bikes, alva)
        self.assertEqual(
            UserResourcePrivilege.get_privilege(
                resource=bikes,
                user=alva),
            PrivilegeCodes.NONE)
        self.assertTrue(is_equal_to_as_set(george.uaccess.get_resource_undo_users(bikes), []))
        self.assertTrue(is_equal_to_as_set(alva.uaccess.get_resource_undo_users(bikes), []))

    def test_can_undo_share_resource_with_user(self):
        george = self.george
        bikes = self.bikes
        alva = self.alva
        self.assertFalse(george.uaccess.can_undo_share_resource_with_user(bikes, alva))
        self.assertFalse(george.uaccess.can_undo_share_resource_with_user(bikes, george))
        self.assertFalse(alva.uaccess.can_undo_share_resource_with_user(bikes, george))
        self.assertEqual(
            UserResourcePrivilege.get_privilege(resource=bikes, user=alva),
            PrivilegeCodes.NONE)
        george.uaccess.share_resource_with_user(bikes, alva, PrivilegeCodes.CHANGE)
        self.assertEqual(
            UserResourcePrivilege.get_privilege(resource=bikes, user=alva),
            PrivilegeCodes.CHANGE)
        self.assertTrue(george.uaccess.can_undo_share_resource_with_user(bikes, alva))
        self.assertFalse(george.uaccess.can_undo_share_resource_with_user(bikes, george))
        self.assertFalse(alva.uaccess.can_undo_share_resource_with_user(bikes, george))
        george.uaccess.undo_share_resource_with_user(bikes, alva)
        self.assertEqual(
            UserResourcePrivilege.get_privilege(resource=bikes, user=alva),
            PrivilegeCodes.NONE)
        self.assertFalse(george.uaccess.can_undo_share_resource_with_user(bikes, alva))
        self.assertFalse(george.uaccess.can_undo_share_resource_with_user(bikes, george))
        self.assertFalse(alva.uaccess.can_undo_share_resource_with_user(bikes, george))
        george.uaccess.share_resource_with_user(bikes, alva, PrivilegeCodes.VIEW)
        self.assertEqual(
            UserResourcePrivilege.get_privilege(resource=bikes, user=alva),
            PrivilegeCodes.VIEW)
        self.assertTrue(george.uaccess.can_undo_share_resource_with_user(bikes, alva))
        self.assertFalse(george.uaccess.can_undo_share_resource_with_user(bikes, george))
        self.assertFalse(alva.uaccess.can_undo_share_resource_with_user(bikes, george))
        george.uaccess.undo_share_resource_with_user(bikes, alva)
        self.assertEqual(
            UserResourcePrivilege.get_privilege(resource=bikes, user=alva),
            PrivilegeCodes.NONE)
        self.assertFalse(george.uaccess.can_undo_share_resource_with_user(bikes, alva))
        self.assertFalse(george.uaccess.can_undo_share_resource_with_user(bikes, george))
        self.assertFalse(alva.uaccess.can_undo_share_resource_with_user(bikes, george))

    def test_undo_share_resource_with_user(self):
        george = self.george
        bikes = self.bikes
        alva = self.alva
        self.assertEqual(
            UserResourcePrivilege.get_privilege(resource=bikes, user=alva),
            PrivilegeCodes.NONE)
        george.uaccess.share_resource_with_user(bikes, alva, PrivilegeCodes.CHANGE)
        self.assertEqual(
            UserResourcePrivilege.get_privilege(resource=bikes, user=alva),
            PrivilegeCodes.CHANGE)
        george.uaccess.undo_share_resource_with_user(bikes, alva)
        self.assertEqual(
            UserResourcePrivilege.get_privilege(resource=bikes, user=alva),
            PrivilegeCodes.NONE)
        george.uaccess.share_resource_with_user(bikes, alva, PrivilegeCodes.VIEW)
        self.assertEqual(
            UserResourcePrivilege.get_privilege(resource=bikes, user=alva),
            PrivilegeCodes.VIEW)
        george.uaccess.undo_share_resource_with_user(bikes, alva)
        self.assertEqual(
            UserResourcePrivilege.get_privilege(resource=bikes, user=alva),
            PrivilegeCodes.NONE)

    def test_get_resource_undo_groups(self):
        george = self.george
        # george.uaccess.get_resource_undo_groups(this_resource)

    def test_can_undo_resource_group_share(self):
        george = self.george
        # george.uaccess.can_undo_resource_group_share(this_resource, this_group)

    def test_undo_share_resource_with_group(self):
        george = self.george
        # george.uaccess.undo_share_resource_with_group(this_resource, this_group)
