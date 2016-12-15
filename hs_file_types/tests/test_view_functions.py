import os
import json
import tempfile
import shutil

from django.core.files.uploadedfile import UploadedFile
from django.test import TestCase, RequestFactory
from django.contrib.auth.models import Group
from django.core.urlresolvers import reverse

from rest_framework import status

from hs_core import hydroshare
from hs_core.hydroshare.utils import resource_post_create_actions
from hs_core.testing import MockIRODSTestCaseMixin
from ..views import set_file_type, add_metadata_element, update_metadata_element, \
    update_key_value_metadata, delete_key_value_metadata
from ..models import GeoRasterLogicalFile


class TestFileTypeViewFunctions(MockIRODSTestCaseMixin, TestCase):
    def setUp(self):
        super(TestFileTypeViewFunctions, self).setUp()
        self.group, _ = Group.objects.get_or_create(name='Hydroshare Author')
        self.username = 'john'
        self.password = 'jhmypassword'
        self.user = hydroshare.create_account(
            'john@gmail.com',
            username=self.username,
            first_name='John',
            last_name='Clarson',
            superuser=False,
            password=self.password,
            groups=[]
        )

        self.composite_resource = hydroshare.create_resource(
            resource_type='CompositeResource',
            owner=self.user,
            title='Test Raster File Metadata'
        )

        self.factory = RequestFactory()

        self.temp_dir = tempfile.mkdtemp()
        self.raster_file_name = 'small_logan.tif'
        self.raster_file = 'hs_file_types/tests/{}'.format(self.raster_file_name)
        target_temp_raster_file = os.path.join(self.temp_dir, self.raster_file_name)
        shutil.copy(self.raster_file, target_temp_raster_file)
        self.raster_file_obj = open(target_temp_raster_file, 'r')

    def tearDown(self):
        super(TestFileTypeViewFunctions, self).tearDown()
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_set_raster_file_type(self):
        # here we are using a valid raster tif file for setting it
        # to Geo Raster file type which includes metadata extraction
        self.raster_file_obj = open(self.raster_file, 'r')
        self._create_composite_resource()

        self.assertEqual(self.composite_resource.files.all().count(), 1)
        res_file = self.composite_resource.files.first()

        # check that the resource file is associated with GenericLogicalFile
        self.assertEqual(res_file.has_logical_file, True)
        self.assertEqual(res_file.logical_file_type_name, "GenericLogicalFile")

        url_params = {'resource_id': self.composite_resource.short_id,
                      'file_id': res_file.id,
                      'hs_file_type': 'GeoRaster'
                      }
        url = reverse('set_file_type', kwargs=url_params)
        request = self.factory.post(url)
        request.user = self.user
        # this is the view function we are testing
        response = set_file_type(request, resource_id=self.composite_resource.short_id,
                                 file_id=res_file.id, hs_file_type='GeoRaster')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_dict = json.loads(response.content)
        self.assertIn("File was successfully set to Geo Raster file type.",
                      response_dict['message'])

        # there should be 2 file now (vrt file was generated by the system
        self.assertEqual(self.composite_resource.files.all().count(), 2)
        res_file = self.composite_resource.files.first()
        self.assertEqual(res_file.logical_file_type_name, "GeoRasterLogicalFile")

    def test_add_update_metadata_to_raster_file_type(self):
        self.raster_file_obj = open(self.raster_file, 'r')
        self._create_composite_resource()
        res_file = self.composite_resource.files.first()

        # set the tif file to GeoRasterFile type
        GeoRasterLogicalFile.set_file_type(self.composite_resource, res_file.id, self.user)
        res_file = self.composite_resource.files.first()
        logical_file = res_file.logical_file

        self.assertEqual(res_file.logical_file_type_name, "GeoRasterLogicalFile")
        # no temporal coverage for the raster file type yet
        self.assertEqual(logical_file.metadata.temporal_coverage, None)
        # add temporal coverage
        url_params = {'hs_file_type': 'GeoRasterLogicalFile',
                      'file_type_id': logical_file.id,
                      'element_name': 'coverage'
                      }
        url = reverse('add_file_metadata', kwargs=url_params)
        request = self.factory.post(url, data={'start': '1/1/2010', 'end': '12/12/2015'})
        request.user = self.user
        # this is the view function we are testing
        response = add_metadata_element(request, hs_file_type="GeoRasterLogicalFile",
                                        file_type_id=logical_file.id, element_name='coverage')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_dict = json.loads(response.content)
        self.assertEqual('success', response_dict['status'])
        # now the raster file should have temporal coverage element
        self.assertNotEqual(logical_file.metadata.temporal_coverage, None)

        # test updating temporal coverage
        url_params['element_id'] = logical_file.metadata.temporal_coverage.id
        url = reverse('update_file_metadata', kwargs=url_params)
        request = self.factory.post(url, data={'start': '1/1/2011', 'end': '12/12/2016'})
        request.user = self.user
        # this is the view function we are testing
        response = update_metadata_element(request, hs_file_type="GeoRasterLogicalFile",
                                           file_type_id=logical_file.id, element_name='coverage',
                                           element_id=logical_file.metadata.temporal_coverage.id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_dict = json.loads(response.content)
        self.assertEqual('success', response_dict['status'])
        temporal_coverage = logical_file.metadata.temporal_coverage
        self.assertEqual(temporal_coverage.value['start'], '2011-01-01')
        self.assertEqual(temporal_coverage.value['end'], '2016-12-12')

    def test_CRUD_key_value_metadata_raster_file_type(self):
        self.raster_file_obj = open(self.raster_file, 'r')
        self._create_composite_resource()
        res_file = self.composite_resource.files.first()

        # set the tif file to GeoRasterFile type
        GeoRasterLogicalFile.set_file_type(self.composite_resource, res_file.id, self.user)
        res_file = self.composite_resource.files.first()
        logical_file = res_file.logical_file

        self.assertEqual(res_file.logical_file_type_name, "GeoRasterLogicalFile")
        # no key/value metadata for the raster file type yet
        self.assertEqual(logical_file.metadata.extra_metadata, {})
        url_params = {'hs_file_type': 'GeoRasterLogicalFile',
                      'file_type_id': logical_file.id
                      }
        url = reverse('update_file_keyvalue_metadata', kwargs=url_params)
        request = self.factory.post(url, data={'key': 'key-1', 'value': 'value-1'})
        request.user = self.user
        # this is the view function we are testing
        response = update_key_value_metadata(request, hs_file_type="GeoRasterLogicalFile",
                                             file_type_id=logical_file.id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_dict = json.loads(response.content)
        self.assertEqual('success', response_dict['status'])
        # there should be key/value metadata for the raster file type yet
        res_file = self.composite_resource.files.first()
        logical_file = res_file.logical_file
        self.assertNotEqual(logical_file.metadata.extra_metadata, {})
        self.assertEqual(logical_file.metadata.extra_metadata['key-1'], 'value-1')

        # update existing key value metadata - updating both key and value
        request = self.factory.post(url, data={'key': 'key-2', 'value': 'value-2',
                                               'key_original': 'key-1'})
        request.user = self.user
        response = update_key_value_metadata(request, hs_file_type="GeoRasterLogicalFile",
                                             file_type_id=logical_file.id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_dict = json.loads(response.content)
        self.assertEqual('success', response_dict['status'])
        res_file = self.composite_resource.files.first()
        logical_file = res_file.logical_file
        self.assertEqual(logical_file.metadata.extra_metadata['key-2'], 'value-2')
        self.assertNotIn('key-1', logical_file.metadata.extra_metadata.keys())

        # update existing key value metadata - updating value only
        request = self.factory.post(url, data={'key': 'key-2', 'value': 'value-1',
                                               'key_original': 'key-2'})
        request.user = self.user
        response = update_key_value_metadata(request, hs_file_type="GeoRasterLogicalFile",
                                             file_type_id=logical_file.id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_dict = json.loads(response.content)
        self.assertEqual('success', response_dict['status'])
        res_file = self.composite_resource.files.first()
        logical_file = res_file.logical_file
        self.assertEqual(logical_file.metadata.extra_metadata['key-2'], 'value-1')

        # delete key/value data using the view function
        request = self.factory.post(url, data={'key': 'key-2'})
        request.user = self.user
        # this the view function we are testing
        response = delete_key_value_metadata(request, hs_file_type="GeoRasterLogicalFile",
                                             file_type_id=logical_file.id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_dict = json.loads(response.content)
        self.assertEqual('success', response_dict['status'])
        res_file = self.composite_resource.files.first()
        logical_file = res_file.logical_file
        # at this point there should not be any key/value metadata
        self.assertEqual(logical_file.metadata.extra_metadata, {})

    def _create_composite_resource(self):
        uploaded_file = UploadedFile(file=self.raster_file_obj,
                                     name=os.path.basename(self.raster_file_obj.name))
        self.composite_resource = hydroshare.create_resource(
            resource_type='CompositeResource',
            owner=self.user,
            title='Test Raster File Type Metadata',
            files=(uploaded_file,)
        )

        # set the generic logical file type
        resource_post_create_actions(resource=self.composite_resource, user=self.user,
                                     metadata=self.composite_resource.metadata)
