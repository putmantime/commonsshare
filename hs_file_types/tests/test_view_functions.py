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
from hs_file_types.views import set_file_type, add_metadata_element, update_metadata_element, \
    update_key_value_metadata, delete_key_value_metadata, add_keyword_metadata, \
    delete_keyword_metadata, update_netcdf_file, update_dataset_name, update_refts_abstract, \
    update_sqlite_file, update_timeseries_abstract, get_timeseries_metadata
from hs_file_types.models import GeoRasterLogicalFile, NetCDFLogicalFile, \
    RefTimeseriesLogicalFile, TimeSeriesLogicalFile


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

        self.netcdf_file_name = 'netcdf_valid.nc'
        self.netcdf_file = 'hs_file_types/tests/{}'.format(self.netcdf_file_name)
        target_temp_netcdf_file = os.path.join(self.temp_dir, self.netcdf_file_name)
        shutil.copy(self.netcdf_file, target_temp_netcdf_file)
        self.netcdf_file_obj = open(target_temp_netcdf_file, 'r')

        self.refts_file_name = 'multi_sites_formatted_version1.0.json.refts'
        self.refts_file = 'hs_file_types/tests/{}'.format(self.refts_file_name)
        target_temp_refts_file = os.path.join(self.temp_dir, self.refts_file_name)
        shutil.copy(self.refts_file, target_temp_refts_file)

        missing_title_refts_json_file = 'refts_valid_title_missing.json.refts'
        self.refts_missing_title_file_name = missing_title_refts_json_file
        self.refts_missing_title_file = 'hs_file_types/tests/{}'.format(
            self.refts_missing_title_file_name)
        target_temp_refts_file = os.path.join(self.temp_dir, self.refts_missing_title_file_name)
        shutil.copy(self.refts_missing_title_file, target_temp_refts_file)

        self.sqlite_file_name = 'ODM2_Multi_Site_One_Variable.sqlite'
        self.sqlite_file = 'hs_file_types/tests/data/{}'.format(self.sqlite_file_name)

        target_temp_sqlite_file = os.path.join(self.temp_dir, self.sqlite_file_name)
        shutil.copy(self.sqlite_file, target_temp_sqlite_file)

    def tearDown(self):
        super(TestFileTypeViewFunctions, self).tearDown()
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_set_raster_file_type(self):
        # here we are using a valid raster tif file for setting it
        # to Geo Raster file type which includes metadata extraction
        self.raster_file_obj = open(self.raster_file, 'r')
        self._create_composite_resource(self.raster_file_obj)

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
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        response_dict = json.loads(response.content)
        self.assertIn("File was successfully set to selected file type.",
                      response_dict['message'])

        # there should be 2 file now (vrt file was generated by the system
        self.assertEqual(self.composite_resource.files.all().count(), 2)
        res_file = self.composite_resource.files.first()
        self.assertEqual(res_file.logical_file_type_name, "GeoRasterLogicalFile")
        self.composite_resource.delete()

    def test_set_netcdf_file_type(self):
        # here we are using a valid netcdf file for setting it
        # to NetCDF file type which includes metadata extraction
        self.netcdf_file_obj = open(self.netcdf_file, 'r')
        self._create_composite_resource(self.netcdf_file_obj)

        self.assertEqual(self.composite_resource.files.all().count(), 1)
        res_file = self.composite_resource.files.first()

        # check that the resource file is associated with GenericLogicalFile
        self.assertEqual(res_file.has_logical_file, True)
        self.assertEqual(res_file.logical_file_type_name, "GenericLogicalFile")

        url_params = {'resource_id': self.composite_resource.short_id,
                      'file_id': res_file.id,
                      'hs_file_type': 'NetCDF'
                      }
        url = reverse('set_file_type', kwargs=url_params)
        request = self.factory.post(url)
        request.user = self.user
        # this is the view function we are testing
        response = set_file_type(request, resource_id=self.composite_resource.short_id,
                                 file_id=res_file.id, hs_file_type='NetCDF')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        response_dict = json.loads(response.content)
        self.assertIn("File was successfully set to selected file type.",
                      response_dict['message'])

        # there should be 2 file now (vrt file was generated by the system
        self.assertEqual(self.composite_resource.files.all().count(), 2)
        res_file = self.composite_resource.files.first()
        self.assertEqual(res_file.logical_file_type_name, "NetCDFLogicalFile")
        self.composite_resource.delete()

    def test_sqlite_set_timeseries_file_type(self):
        # here we are using a valid sqlite file for setting it
        # to TimeSeries file type which includes metadata extraction
        self.sqlite_file_obj = open(self.sqlite_file, 'r')
        self._create_composite_resource(self.sqlite_file_obj)

        self.assertEqual(self.composite_resource.files.all().count(), 1)
        res_file = self.composite_resource.files.first()

        # check that the resource file is associated with GenericLogicalFile
        self.assertEqual(res_file.has_logical_file, True)
        self.assertEqual(res_file.logical_file_type_name, "GenericLogicalFile")

        url_params = {'resource_id': self.composite_resource.short_id,
                      'file_id': res_file.id,
                      'hs_file_type': 'TimeSeries'
                      }
        url = reverse('set_file_type', kwargs=url_params)
        request = self.factory.post(url)
        request.user = self.user
        # this is the view function we are testing
        response = set_file_type(request, resource_id=self.composite_resource.short_id,
                                 file_id=res_file.id, hs_file_type='TimeSeries')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        response_dict = json.loads(response.content)
        self.assertIn("File was successfully set to selected file type.",
                      response_dict['message'])

        # there should be still 1 file now (sqlite file)
        self.assertEqual(self.composite_resource.files.all().count(), 1)
        res_file = self.composite_resource.files.first()
        self.assertEqual(res_file.logical_file_type_name, "TimeSeriesLogicalFile")
        self.composite_resource.delete()

    def test_add_update_metadata_to_raster_file_type(self):
        self.raster_file_obj = open(self.raster_file, 'r')
        self._create_composite_resource(self.raster_file_obj)
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
        self.composite_resource.delete()

    def test_add_update_metadata_to_netcdf_file_type(self):
        self.netcdf_file_obj = open(self.netcdf_file, 'r')
        self._create_composite_resource(self.netcdf_file_obj)
        res_file = self.composite_resource.files.first()

        # set the nc file to NetCDF File type
        NetCDFLogicalFile.set_file_type(self.composite_resource, res_file.id, self.user)
        res_file = self.composite_resource.files.first()
        logical_file = res_file.logical_file

        self.assertEqual(res_file.logical_file_type_name, "NetCDFLogicalFile")
        # there should be temporal coverage for the netcdf file type
        self.assertNotEqual(logical_file.metadata.temporal_coverage, None)
        temporal_coverage = logical_file.metadata.temporal_coverage
        self.assertEqual(temporal_coverage.value['start'], '2009-10-01 00:00:00')
        self.assertEqual(temporal_coverage.value['end'], '2010-05-30 23:00:00')

        url_params = {'hs_file_type': 'NetCDFLogicalFile',
                      'file_type_id': logical_file.id,
                      'element_name': 'coverage',
                      'element_id': logical_file.metadata.temporal_coverage.id
                      }

        # test updating temporal coverage
        url = reverse('update_file_metadata', kwargs=url_params)
        request = self.factory.post(url, data={'start': '1/1/2011', 'end': '12/12/2016'})
        request.user = self.user
        # this is the view function we are testing
        response = update_metadata_element(request, hs_file_type="NetCDFLogicalFile",
                                           file_type_id=logical_file.id, element_name='coverage',
                                           element_id=logical_file.metadata.temporal_coverage.id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_dict = json.loads(response.content)
        self.assertEqual('success', response_dict['status'])
        temporal_coverage = logical_file.metadata.temporal_coverage
        self.assertEqual(temporal_coverage.value['start'], '2011-01-01')
        self.assertEqual(temporal_coverage.value['end'], '2016-12-12')

        # test updating OriginalCoverage element
        # there should be original coverage for the netcdf file type
        self.assertNotEqual(logical_file.metadata.original_coverage, None)
        orig_coverage = logical_file.metadata.original_coverage
        self.assertEqual(orig_coverage.value['northlimit'], '4.63515e+06')

        coverage_data = {'northlimit': '111.333', 'southlimit': '42.678', 'eastlimit': '123.789',
                         'westlimit': '40.789', 'units': 'meters'}
        url_params['element_name'] = 'originalcoverage'
        url_params['element_id'] = logical_file.metadata.original_coverage.id
        url = reverse('update_file_metadata', kwargs=url_params)
        request = self.factory.post(url, data=coverage_data)
        request.user = self.user
        # this is the view function we are testing
        response = update_metadata_element(request, hs_file_type="NetCDFLogicalFile",
                                           file_type_id=logical_file.id,
                                           element_name='originalcoverage',
                                           element_id=logical_file.metadata.original_coverage.id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_dict = json.loads(response.content)
        self.assertEqual('success', response_dict['status'])
        orig_coverage = logical_file.metadata.original_coverage
        self.assertEqual(orig_coverage.value['northlimit'], '111.333')

        # test updating spatial coverage
        # there should be spatial coverage for the netcdf file type
        self.assertNotEqual(logical_file.metadata.spatial_coverage, None)
        spatial_coverage = logical_file.metadata.spatial_coverage
        self.assertEqual(spatial_coverage.value['northlimit'], 41.867126409)

        coverage_data = {'type': 'box', 'projection': 'WGS 84 EPSG:4326', 'northlimit': '41.87',
                         'southlimit': '41.863',
                         'eastlimit': '-111.505',
                         'westlimit': '-111.511', 'units': 'meters'}

        url_params['element_name'] = 'coverage'
        url_params['element_id'] = spatial_coverage.id
        url = reverse('update_file_metadata', kwargs=url_params)
        request = self.factory.post(url, data=coverage_data)
        request.user = self.user
        # this is the view function we are testing
        response = update_metadata_element(request, hs_file_type="NetCDFLogicalFile",
                                           file_type_id=logical_file.id,
                                           element_name='coverage',
                                           element_id=spatial_coverage.id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_dict = json.loads(response.content)
        self.assertEqual('success', response_dict['status'])
        spatial_coverage = logical_file.metadata.spatial_coverage
        self.assertEqual(spatial_coverage.value['northlimit'], 41.87)

        # test update Variable element
        variable = logical_file.metadata.variables.first()
        variable_data = {'name': 'variable_name_updated', 'type': 'Int', 'unit': 'deg F',
                         'shape': 'variable_shape'}

        url_params['element_name'] = 'variable'
        url_params['element_id'] = variable.id
        url = reverse('update_file_metadata', kwargs=url_params)
        request = self.factory.post(url, data=variable_data)
        request.user = self.user
        # this is the view function we are testing
        response = update_metadata_element(request, hs_file_type="NetCDFLogicalFile",
                                           file_type_id=logical_file.id,
                                           element_name='variable',
                                           element_id=variable.id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_dict = json.loads(response.content)
        self.assertEqual('success', response_dict['status'])
        variable = logical_file.metadata.variables.all().filter(id=variable.id).first()
        self.assertEqual(variable.name, 'variable_name_updated')

        self.composite_resource.delete()

    def test_update_dataset_name_raster_file_type(self):
        self.raster_file_obj = open(self.raster_file, 'r')
        self._create_composite_resource(self.raster_file_obj)
        res_file = self.composite_resource.files.first()

        # set the tif file to GeoRasterFile type
        GeoRasterLogicalFile.set_file_type(self.composite_resource, res_file.id, self.user)
        res_file = self.composite_resource.files.first()
        logical_file = res_file.logical_file

        self.assertEqual(res_file.logical_file_type_name, "GeoRasterLogicalFile")
        # check dataset_name before updating via the view function
        self.assertEqual(logical_file.dataset_name, "small_logan")
        url_params = {'hs_file_type': 'GeoRasterLogicalFile',
                      'file_type_id': logical_file.id
                      }
        url = reverse('update_filetype_datatset_name', kwargs=url_params)
        request = self.factory.post(url, data={'dataset_name': 'Logan River'})
        request.user = self.user
        # this is the view function we are testing
        response = update_dataset_name(request, hs_file_type="GeoRasterLogicalFile",
                                       file_type_id=logical_file.id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_dict = json.loads(response.content)
        self.assertEqual('success', response_dict['status'])
        # check dataset_name after updating via the view function
        res_file = self.composite_resource.files.first()
        logical_file = res_file.logical_file
        self.assertEqual(logical_file.dataset_name, "Logan River")

        self.composite_resource.delete()

    def test_update_dataset_name_netcdf_file_type(self):
        self.netcdf_file_obj = open(self.netcdf_file, 'r')
        self._create_composite_resource(self.netcdf_file_obj)
        res_file = self.composite_resource.files.first()

        # set the nc file to NetCDF File type
        NetCDFLogicalFile.set_file_type(self.composite_resource, res_file.id, self.user)
        res_file = self.composite_resource.files.first()
        logical_file = res_file.logical_file

        self.assertEqual(res_file.logical_file_type_name, "NetCDFLogicalFile")
        # check dataset_name before updating via the view function
        dataset_name = "Snow water equivalent estimation at TWDEF site from Oct 2009 to June 2010"
        self.assertEqual(logical_file.dataset_name, dataset_name)
        url_params = {'hs_file_type': 'NetCDFLogicalFile',
                      'file_type_id': logical_file.id
                      }
        url = reverse('update_filetype_datatset_name', kwargs=url_params)
        dataset_name = "Snow water equivalent estimation at TWDEF site from Oct 20010 to June 2015"
        request = self.factory.post(url, data={'dataset_name': dataset_name})
        request.user = self.user
        # this is the view function we are testing
        response = update_dataset_name(request, hs_file_type="NetCDFLogicalFile",
                                       file_type_id=logical_file.id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_dict = json.loads(response.content)
        self.assertEqual('success', response_dict['status'])
        # check dataset_name after updating via the view function
        res_file = self.composite_resource.files.first()
        logical_file = res_file.logical_file
        self.assertEqual(logical_file.dataset_name, dataset_name)

        self.composite_resource.delete()

    def test_update_dataset_name_refts_file_type_failure(self):
        # we should not be able to update dataset name since the json file
        # has the title element
        self.refts_file_obj = open(self.refts_file, 'r')
        self._create_composite_resource(self.refts_file_obj)
        res_file = self.composite_resource.files.first()

        # set the json file to RefTimeSeries File type
        RefTimeseriesLogicalFile.set_file_type(self.composite_resource, res_file.id, self.user)
        res_file = self.composite_resource.files.first()
        logical_file = res_file.logical_file

        self.assertEqual(res_file.logical_file_type_name, "RefTimeseriesLogicalFile")
        # check dataset_name before updating via the view function
        orig_dataset_name = "Sites, Variable"
        self.assertEqual(logical_file.dataset_name, orig_dataset_name)
        url_params = {'hs_file_type': 'RefTimeseriesLogicalFile',
                      'file_type_id': logical_file.id
                      }
        url = reverse('update_filetype_datatset_name', kwargs=url_params)
        dataset_name = "Multiple sites with one variable"
        request = self.factory.post(url, data={'dataset_name': dataset_name})
        request.user = self.user
        # this is the view function we are testing
        response = update_dataset_name(request, hs_file_type="RefTimeseriesLogicalFile",
                                       file_type_id=logical_file.id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_dict = json.loads(response.content)
        self.assertEqual('error', response_dict['status'])
        # check dataset_name after updating via the view function
        res_file = self.composite_resource.files.first()
        logical_file = res_file.logical_file
        # dataset name should not have changed
        self.assertNotEqual(logical_file.dataset_name, dataset_name)
        self.assertEqual(logical_file.dataset_name, orig_dataset_name)
        self.composite_resource.delete()

    def test_update_dataset_name_refts_file_type_success(self):
        # we should be able to update dataset name since the json file
        # does not have the title element
        self.refts_missing_title_file_obj = open(self.refts_missing_title_file, 'r')
        self._create_composite_resource(self.refts_missing_title_file_obj)
        res_file = self.composite_resource.files.first()

        # set the json file to RefTimeSeries File type
        RefTimeseriesLogicalFile.set_file_type(self.composite_resource, res_file.id, self.user)
        res_file = self.composite_resource.files.first()
        logical_file = res_file.logical_file
        self.assertFalse(logical_file.metadata.has_title_in_json)
        self.assertEqual(res_file.logical_file_type_name, "RefTimeseriesLogicalFile")
        # check dataset_name before updating via the view function
        orig_dataset_name = ""
        self.assertEqual(logical_file.dataset_name, orig_dataset_name)
        url_params = {'hs_file_type': 'RefTimeseriesLogicalFile',
                      'file_type_id': logical_file.id
                      }
        url = reverse('update_filetype_datatset_name', kwargs=url_params)
        dataset_name = "Multiple sites with one variable"
        request = self.factory.post(url, data={'dataset_name': dataset_name})
        request.user = self.user
        # this is the view function we are testing
        response = update_dataset_name(request, hs_file_type="RefTimeseriesLogicalFile",
                                       file_type_id=logical_file.id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_dict = json.loads(response.content)
        self.assertEqual('success', response_dict['status'])
        # check dataset_name after updating via the view function
        res_file = self.composite_resource.files.first()
        logical_file = res_file.logical_file
        # dataset name should have been changed
        self.assertEqual(logical_file.dataset_name, dataset_name)
        self.composite_resource.delete()

    def test_update_abstract_refts_failure(self):
        # we should not be able to update abstract since the json file
        # has the abstract element
        self.refts_file_obj = open(self.refts_file, 'r')
        self._create_composite_resource(self.refts_file_obj)
        res_file = self.composite_resource.files.first()

        # set the json file to RefTimeSeries File type
        RefTimeseriesLogicalFile.set_file_type(self.composite_resource, res_file.id, self.user)
        res_file = self.composite_resource.files.first()
        logical_file = res_file.logical_file

        self.assertEqual(res_file.logical_file_type_name, "RefTimeseriesLogicalFile")
        # test that the abstract key is in json file
        self.assertTrue(logical_file.metadata.has_abstract_in_json)
        # check abstract before updating via the view function
        orig_abstract = "Discharge, cubic feet per second,Blue-green algae (cyanobacteria), " \
                        "phycocyanin data collected from 2016-04-06 to 2017-02-09 created on " \
                        "Thu Apr 06 2017 09:15:56 GMT-0600 (Mountain Daylight Time) from the " \
                        "following site(s): HOBBLE CREEK AT 1650 WEST AT SPRINGVILLE, UTAH, and " \
                        "Provo River at Charleston Advanced Aquatic. Data created by " \
                        "CUAHSI HydroClient: http://data.cuahsi.org/#."
        self.assertEqual(logical_file.metadata.abstract, orig_abstract)
        url_params = {'file_type_id': logical_file.id}
        url = reverse('update_reftimeseries_abstract', kwargs=url_params)
        new_abstract = "Discharge, cubic feet per second,Blue-green algae (cyanobacteria)"
        request = self.factory.post(url, data={'abstract': new_abstract})
        request.user = self.user
        # this is the view function we are testing
        response = update_refts_abstract(request, file_type_id=logical_file.id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_dict = json.loads(response.content)
        self.assertEqual('error', response_dict['status'])
        # check abstract after updating via the view function
        res_file = self.composite_resource.files.first()
        logical_file = res_file.logical_file
        # abstract should not have changed
        self.assertNotEqual(logical_file.metadata.abstract, new_abstract)
        self.assertEqual(logical_file.metadata.abstract, orig_abstract)
        self.composite_resource.delete()

    def test_update_abstract_refts_success(self):
        # we should be able to update abstract since the json file
        # does't have the abstract element
        self.refts_missing_abstract_file_name = 'refts_valid_abstract_missing.json.refts'
        self.refts_missing_abstract_file = 'hs_file_types/tests/{}'.format(
            self.refts_missing_abstract_file_name)

        tgt_temp_refts_abstract_file = os.path.join(
            self.temp_dir, self.refts_missing_abstract_file_name)
        shutil.copy(self.refts_missing_abstract_file, tgt_temp_refts_abstract_file)
        self.refts_file_obj = open(self.refts_missing_abstract_file, 'r')
        self._create_composite_resource(self.refts_file_obj)
        res_file = self.composite_resource.files.first()

        # set the json file to RefTimeSeries File type
        RefTimeseriesLogicalFile.set_file_type(self.composite_resource, res_file.id, self.user)
        res_file = self.composite_resource.files.first()
        logical_file = res_file.logical_file

        self.assertEqual(res_file.logical_file_type_name, "RefTimeseriesLogicalFile")
        # test that the abstract key is not in json file
        self.assertFalse(logical_file.metadata.has_abstract_in_json)
        self.assertEqual(logical_file.metadata.abstract, "")
        url_params = {'file_type_id': logical_file.id}
        url = reverse('update_reftimeseries_abstract', kwargs=url_params)
        new_abstract = "Discharge, cubic feet per second,Blue-green algae (cyanobacteria)"
        request = self.factory.post(url, data={'abstract': new_abstract})
        request.user = self.user
        # this is the view function we are testing
        response = update_refts_abstract(request, file_type_id=logical_file.id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_dict = json.loads(response.content)
        self.assertEqual('success', response_dict['status'])
        # check abstract after updating via the view function
        res_file = self.composite_resource.files.first()
        logical_file = res_file.logical_file
        # abstract should have changed
        self.assertEqual(logical_file.metadata.abstract, new_abstract)
        self.composite_resource.delete()

    def test_update_abstract_timeseries(self):
        # we should be able to update abstract for time series file type
        # does't have the abstract element
        self.sqlite_file_obj = open(self.sqlite_file, 'r')
        self._create_composite_resource(self.sqlite_file_obj)

        self.assertEqual(self.composite_resource.files.all().count(), 1)
        res_file = self.composite_resource.files.first()

        # set the sqlite file to TimeSeries file type
        TimeSeriesLogicalFile.set_file_type(self.composite_resource, res_file.id, self.user)
        res_file = self.composite_resource.files.first()
        logical_file = res_file.logical_file

        self.assertEqual(res_file.logical_file_type_name, "TimeSeriesLogicalFile")
        url_params = {'file_type_id': logical_file.id}
        url = reverse('update_timeseries_abstract', kwargs=url_params)
        new_abstract = "Discharge, cubic feet per second,Blue-green algae (cyanobacteria)"
        request = self.factory.post(url, data={'abstract': new_abstract})
        request.user = self.user
        # this is the view function we are testing
        response = update_timeseries_abstract(request, file_type_id=logical_file.id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_dict = json.loads(response.content)
        self.assertEqual('success', response_dict['status'])
        # check abstract after updating via the view function
        res_file = self.composite_resource.files.first()
        logical_file = res_file.logical_file
        # abstract should have changed
        self.assertEqual(logical_file.metadata.abstract, new_abstract)
        self.composite_resource.delete()

    def test_get_timeseries_metadata(self):
        # we should be able to update abstract for time series file type
        # does't have the abstract element
        self.sqlite_file_obj = open(self.sqlite_file, 'r')
        self._create_composite_resource(self.sqlite_file_obj)

        self.assertEqual(self.composite_resource.files.all().count(), 1)
        res_file = self.composite_resource.files.first()

        # set the sqlite file to TimeSeries file type
        TimeSeriesLogicalFile.set_file_type(self.composite_resource, res_file.id, self.user)
        res_file = self.composite_resource.files.first()
        logical_file = res_file.logical_file

        self.assertEqual(res_file.logical_file_type_name, "TimeSeriesLogicalFile")
        series_id = logical_file.metadata.sites.first().series_ids[0]
        url_params = {'file_type_id': logical_file.id, 'series_id': series_id,
                      'resource_mode': 'edit'}
        url = reverse('get_timeseries_file_metadata', kwargs=url_params)
        new_abstract = "Discharge, cubic feet per second,Blue-green algae (cyanobacteria)"
        request = self.factory.post(url, data={'abstract': new_abstract})
        request.user = self.user
        # this is the view function we are testing
        response = get_timeseries_metadata(request, file_type_id=logical_file.id,
                                           series_id=series_id, resource_mode='edit')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_dict = json.loads(response.content)
        self.assertEqual('success', response_dict['status'])
        self.composite_resource.delete()

    def test_add_delete_keywords_refts_failure(self):
        # we should not be able to add/delete keywords since the json file
        # has the keywords element
        self.refts_file_obj = open(self.refts_file, 'r')
        self._create_composite_resource(self.refts_file_obj)
        res_file = self.composite_resource.files.first()
        file_type = 'RefTimeseriesLogicalFile'
        # set the json file to RefTimeSeries File type
        RefTimeseriesLogicalFile.set_file_type(self.composite_resource, res_file.id, self.user)
        res_file = self.composite_resource.files.first()
        logical_file = res_file.logical_file

        self.assertEqual(res_file.logical_file_type_name, file_type)
        # test that the keywords key is in json file
        self.assertTrue(logical_file.metadata.has_keywords_in_json)
        # check keywords before adding via the view function
        for kw in ('Time Series', 'CUAHSI'):
            self.assertIn(kw, logical_file.metadata.keywords)
        # add keywords at the file level
        url_params = {'hs_file_type': file_type,
                      'file_type_id': logical_file.id
                      }
        url = reverse('add_file_keyword_metadata', kwargs=url_params)
        request = self.factory.post(url, data={'keywords': 'keyword-1,keyword-2'})
        request.user = self.user
        # this is the view function we are testing
        response = add_keyword_metadata(request, hs_file_type=file_type,
                                        file_type_id=logical_file.id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_dict = json.loads(response.content)
        self.assertEqual('error', response_dict['status'])
        self.assertEqual(len(logical_file.metadata.keywords), 2)
        # check keywords after adding via the view function- should not have changed
        for kw in ('Time Series', 'CUAHSI'):
            self.assertIn(kw, logical_file.metadata.keywords)

        # delete keyword
        url = reverse('delete_file_keyword_metadata', kwargs=url_params)
        request = self.factory.post(url, data={'keyword': 'CUAHSI'})
        request.user = self.user
        # this is the view function we are testing
        response = delete_keyword_metadata(request, hs_file_type=file_type,
                                           file_type_id=logical_file.id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_dict = json.loads(response.content)
        self.assertEqual('error', response_dict['status'])

        res_file = self.composite_resource.files.first()
        logical_file = res_file.logical_file
        self.assertEqual(len(logical_file.metadata.keywords), 2)
        # check keywords after deleting via the view function- should not have changed
        for kw in ('Time Series', 'CUAHSI'):
            self.assertIn(kw, logical_file.metadata.keywords)
        self.composite_resource.delete()

    def test_add_delete_keywords_refts_success(self):
        # we should be able to add/delete keywords since the json file
        # does not have the keywords element
        self.refts_missing_keywords_file_name = 'refts_valid_keywords_missing.json.refts'
        self.refts_missing_keywords_file = 'hs_file_types/tests/{}'.format(
            self.refts_missing_keywords_file_name)

        tgt_temp_refts_missing_keywords_file = os.path.join(
            self.temp_dir, self.refts_missing_keywords_file_name)
        shutil.copy(self.refts_missing_keywords_file, tgt_temp_refts_missing_keywords_file)
        self.refts_file_obj = open(tgt_temp_refts_missing_keywords_file, 'r')
        self._create_composite_resource(self.refts_file_obj)
        res_file = self.composite_resource.files.first()
        file_type = 'RefTimeseriesLogicalFile'
        # set the json file to RefTimeSeries File type
        RefTimeseriesLogicalFile.set_file_type(self.composite_resource, res_file.id, self.user)
        res_file = self.composite_resource.files.first()
        logical_file = res_file.logical_file

        self.assertEqual(res_file.logical_file_type_name, file_type)
        # test that the keywords key is not in json file
        self.assertFalse(logical_file.metadata.has_keywords_in_json)
        self.assertEqual(len(logical_file.metadata.keywords), 0)

        # add keywords at the file level
        url_params = {'hs_file_type': file_type,
                      'file_type_id': logical_file.id
                      }
        url = reverse('add_file_keyword_metadata', kwargs=url_params)
        request = self.factory.post(url, data={'keywords': 'keyword-1,keyword-2'})
        request.user = self.user
        # this is the view function we are testing
        response = add_keyword_metadata(request, hs_file_type=file_type,
                                        file_type_id=logical_file.id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_dict = json.loads(response.content)
        self.assertEqual('success', response_dict['status'])
        # check keywords after adding via the view function- should have keywords now
        res_file = self.composite_resource.files.first()
        logical_file = res_file.logical_file
        self.assertEqual(len(logical_file.metadata.keywords), 2)
        for kw in ('keyword-1', 'keyword-2'):
            self.assertIn(kw, logical_file.metadata.keywords)

        # delete keyword
        url = reverse('delete_file_keyword_metadata', kwargs=url_params)
        request = self.factory.post(url, data={'keyword': 'keyword-1'})
        request.user = self.user
        # this is the view function we are testing
        response = delete_keyword_metadata(request, hs_file_type=file_type,
                                           file_type_id=logical_file.id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_dict = json.loads(response.content)
        self.assertEqual('success', response_dict['status'])

        # check keywords after deleting via the view function- one keyword should have been deleted
        res_file = self.composite_resource.files.first()
        logical_file = res_file.logical_file
        self.assertEqual(len(logical_file.metadata.keywords), 1)
        self.assertIn('keyword-2', logical_file.metadata.keywords)

        self.composite_resource.delete()

    def test_CRUD_key_value_metadata_raster_file_type(self):
        self.raster_file_obj = open(self.raster_file, 'r')
        self._create_composite_resource(self.raster_file_obj)
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
        self.composite_resource.delete()

    def test_CRUD_key_value_metadata_netcdf_file_type(self):
        self.netcdf_file_obj = open(self.netcdf_file, 'r')
        self._create_composite_resource(self.netcdf_file_obj)
        res_file = self.composite_resource.files.first()

        # set the nc file to NetCDF file type
        NetCDFLogicalFile.set_file_type(self.composite_resource, res_file.id, self.user)
        res_file = self.composite_resource.files.first()
        logical_file = res_file.logical_file

        self.assertEqual(res_file.logical_file_type_name, "NetCDFLogicalFile")
        # no key/value metadata for the netcdf file type yet
        self.assertEqual(logical_file.metadata.extra_metadata, {})
        url_params = {'hs_file_type': 'NetCDFLogicalFile',
                      'file_type_id': logical_file.id
                      }
        url = reverse('update_file_keyvalue_metadata', kwargs=url_params)
        request = self.factory.post(url, data={'key': 'key-1', 'value': 'value-1'})
        request.user = self.user
        # this is the view function we are testing
        response = update_key_value_metadata(request, hs_file_type="NetCDFLogicalFile",
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
        response = update_key_value_metadata(request, hs_file_type="NetCDFLogicalFile",
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
        response = update_key_value_metadata(request, hs_file_type="NetCDFLogicalFile",
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
        response = delete_key_value_metadata(request, hs_file_type="NetCDFLogicalFile",
                                             file_type_id=logical_file.id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_dict = json.loads(response.content)
        self.assertEqual('success', response_dict['status'])
        res_file = self.composite_resource.files.first()
        logical_file = res_file.logical_file
        # at this point there should not be any key/value metadata
        self.assertEqual(logical_file.metadata.extra_metadata, {})
        self.composite_resource.delete()

    def test_add_delete_keywords_file_types(self):
        # test adding and deleting of keywords
        # test for raster file type
        self.raster_file_obj = open(self.raster_file, 'r')
        self._add_delete_keywords_file_type(self.raster_file_obj, 'GeoRasterLogicalFile')
        # test for netcdf file type
        self.netcdf_file_obj = open(self.netcdf_file, 'r')
        self._add_delete_keywords_file_type(self.netcdf_file_obj, 'NetCDFLogicalFile')

    def test_update_netcdf_file(self):
        self.netcdf_file_obj = open(self.netcdf_file, 'r')
        self._create_composite_resource(self.netcdf_file_obj)
        res_file = self.composite_resource.files.first()

        # set the nc file to NetCDF file type
        NetCDFLogicalFile.set_file_type(self.composite_resource, res_file.id, self.user)
        res_file = self.composite_resource.files.first()
        logical_file = res_file.logical_file

        self.assertEqual(res_file.logical_file_type_name, "NetCDFLogicalFile")
        # one keyword metadata for the netcdf file type
        self.assertEqual(len(logical_file.metadata.keywords), 1)
        nc_dump_res_file = None
        for f in logical_file.files.all():
            if f.extension == ".txt":
                nc_dump_res_file = f
                break
        self.assertNotEqual(nc_dump_res_file, None)
        self.assertIn('keywords = "Snow water equivalent"', nc_dump_res_file.resource_file.read())
        logical_file.metadata.keywords = ["keyword-1", 'keyword-2']
        logical_file.metadata.save()
        url_params = {'file_type_id': logical_file.id}
        url = reverse('update_netcdf_file', kwargs=url_params)
        request = self.factory.post(url, data={})
        request.user = self.user
        # this is the view function we are testing
        response = update_netcdf_file(request, file_type_id=logical_file.id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_dict = json.loads(response.content)
        self.assertEqual('success', response_dict['status'])
        # ncdump file gets regenerated as part of the netcdf file update
        for f in logical_file.files.all():
            if f.extension == ".txt":
                nc_dump_res_file = f
                break
        self.assertNotEqual(nc_dump_res_file, None)
        self.assertIn('keywords = "keyword-1, keyword-2"', nc_dump_res_file.resource_file.read())
        self.composite_resource.delete()

    def test_update_sqlite_file(self):
        """test updating sqlite file for timeseries file type"""
        self.sqlite_file_obj = open(self.sqlite_file, 'r')
        self._create_composite_resource(self.sqlite_file_obj)
        res_file = self.composite_resource.files.first()
        # set the sqlite file to TimeSeries file type
        TimeSeriesLogicalFile.set_file_type(self.composite_resource, res_file.id, self.user)
        res_file = self.composite_resource.files.first()
        logical_file = res_file.logical_file
        logical_file.metadata.abstract = "new abstract for time series file type"
        logical_file.metadata.is_dirty = True
        logical_file.metadata.save()

        url_params = {'file_type_id': logical_file.id}
        url = reverse('update_sqlite_file', kwargs=url_params)
        request = self.factory.post(url, data={})
        request.user = self.user
        # this is the view function we are testing
        response = update_sqlite_file(request, file_type_id=logical_file.id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_dict = json.loads(response.content)
        self.assertEqual('success', response_dict['status'])
        self.composite_resource.delete()

    def _add_delete_keywords_file_type(self, file_obj, file_type):
        self._create_composite_resource(file_obj)
        res_file = self.composite_resource.files.first()

        # set specific file type
        if file_type == "GeoRasterLogicalFile":
            GeoRasterLogicalFile.set_file_type(self.composite_resource, res_file.id, self.user)
        else:
            NetCDFLogicalFile.set_file_type(self.composite_resource, res_file.id, self.user)

        res_file = self.composite_resource.files.first()
        logical_file = res_file.logical_file

        self.assertEqual(res_file.logical_file_type_name, file_type)

        if file_type != "NetCDFLogicalFile":
            # no keyword metadata for the raster file type yet
            self.assertEqual(len(logical_file.metadata.keywords), 0)
        else:
            # one keyword metadata for the netcdf file type
            self.assertEqual(len(logical_file.metadata.keywords), 1)

        # at this point resource should have all the keywords that we have for the file type
        res_keywords = [subject.value for subject in
                        self.composite_resource.metadata.subjects.all()]

        for kw in logical_file.metadata.keywords:
            self.assertIn(kw, res_keywords)

        # add keywords at the file level
        url_params = {'hs_file_type': file_type,
                      'file_type_id': logical_file.id
                      }
        url = reverse('add_file_keyword_metadata', kwargs=url_params)
        request = self.factory.post(url, data={'keywords': 'keyword-1,keyword-2'})
        request.user = self.user
        # this is the view function we are testing
        response = add_keyword_metadata(request, hs_file_type=file_type,
                                        file_type_id=logical_file.id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_dict = json.loads(response.content)
        self.assertEqual('success', response_dict['status'])

        # there should be 2 keywords for the raster file type yet
        res_file = self.composite_resource.files.first()
        logical_file = res_file.logical_file
        if file_type != "NetCDFLogicalFile":
            self.assertEqual(len(logical_file.metadata.keywords), 2)
        else:
            self.assertEqual(len(logical_file.metadata.keywords), 3)

        self.assertIn('keyword-1', logical_file.metadata.keywords)
        self.assertIn('keyword-2', logical_file.metadata.keywords)

        # resource level keywords must have been updated with the keywords we added
        # to file level
        res_keywords = [subject.value for subject in
                        self.composite_resource.metadata.subjects.all()]

        for kw in logical_file.metadata.keywords:
            self.assertIn(kw, res_keywords)

        # delete keyword
        url = reverse('delete_file_keyword_metadata', kwargs=url_params)
        request = self.factory.post(url, data={'keyword': 'keyword-1'})
        request.user = self.user
        # this is the view function we are testing
        response = delete_keyword_metadata(request, hs_file_type=file_type,
                                           file_type_id=logical_file.id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_dict = json.loads(response.content)
        self.assertEqual('success', response_dict['status'])

        res_file = self.composite_resource.files.first()
        logical_file = res_file.logical_file
        if file_type != "NetCDFLogicalFile":
            self.assertEqual(len(logical_file.metadata.keywords), 1)
        else:
            self.assertEqual(len(logical_file.metadata.keywords), 2)

        self.assertIn('keyword-2', logical_file.metadata.keywords)

        # test that deleting a file level keyword doesn't delete the same keyword from
        # resource level
        self.assertIn('keyword-1', res_keywords)
        self.composite_resource.delete()

    def _create_composite_resource(self, file_obj):
        uploaded_file = UploadedFile(file=file_obj,
                                     name=os.path.basename(file_obj.name))
        self.composite_resource = hydroshare.create_resource(
            resource_type='CompositeResource',
            owner=self.user,
            title='Test Raster File Type Metadata',
            files=(uploaded_file,)
        )

        # set the generic logical file type
        resource_post_create_actions(resource=self.composite_resource, user=self.user,
                                     metadata=self.composite_resource.metadata)
