# coding: utf-8

"""
    Jobbergate-API

    No description provided (generated by Openapi Generator https://github.com/openapitools/openapi-generator)

    The version of the OpenAPI document: 4.3.0a1
    Contact: info@omnivector.solutions
    Generated by OpenAPI Generator (https://openapi-generator.tech)

    Do not edit the class manually.
"""  # noqa: E501


import unittest
import datetime

from openapi_client.models.page_job_script_list_view import PageJobScriptListView  # noqa: E501

class TestPageJobScriptListView(unittest.TestCase):
    """PageJobScriptListView unit test stubs"""

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def make_instance(self, include_optional) -> PageJobScriptListView:
        """Test PageJobScriptListView
            include_option is a boolean, when False only required
            params are included, when True both required and
            optional params are included """
        # uncomment below to create an instance of `PageJobScriptListView`
        """
        model = PageJobScriptListView()  # noqa: E501
        if include_optional:
            return PageJobScriptListView(
                items = [
                    openapi_client.models.job_script_list_view.JobScriptListView(
                        id = 101, 
                        name = 'test-job-script-88', 
                        owner_email = 'tucker@omnivector.solutions', 
                        created_at = '2023-08-18T13:55:37.172285', 
                        updated_at = '2023-08-18T13:55:37.172285', 
                        is_archived = False, 
                        description = 'This job_scripts runs an Foo job using the bar variant', 
                        parent_template_id = 71, 
                        template = openapi_client.models.job_template_list_view.JobTemplateListView(
                            id = 101, 
                            name = 'test-job-script-88', 
                            owner_email = 'tucker@omnivector.solutions', 
                            created_at = '2023-08-18T13:55:37.172285', 
                            updated_at = '2023-08-18T13:55:37.172285', 
                            is_archived = False, 
                            description = 'This job_scripts runs an Foo job using the bar variant', 
                            identifier = 'App88', 
                            cloned_from_id = 101, ), 
                        cloned_from_id = 101, )
                    ],
                total = 0.0,
                page = 1.0,
                size = 1.0,
                pages = 0.0
            )
        else:
            return PageJobScriptListView(
                items = [
                    openapi_client.models.job_script_list_view.JobScriptListView(
                        id = 101, 
                        name = 'test-job-script-88', 
                        owner_email = 'tucker@omnivector.solutions', 
                        created_at = '2023-08-18T13:55:37.172285', 
                        updated_at = '2023-08-18T13:55:37.172285', 
                        is_archived = False, 
                        description = 'This job_scripts runs an Foo job using the bar variant', 
                        parent_template_id = 71, 
                        template = openapi_client.models.job_template_list_view.JobTemplateListView(
                            id = 101, 
                            name = 'test-job-script-88', 
                            owner_email = 'tucker@omnivector.solutions', 
                            created_at = '2023-08-18T13:55:37.172285', 
                            updated_at = '2023-08-18T13:55:37.172285', 
                            is_archived = False, 
                            description = 'This job_scripts runs an Foo job using the bar variant', 
                            identifier = 'App88', 
                            cloned_from_id = 101, ), 
                        cloned_from_id = 101, )
                    ],
                total = 0.0,
        )
        """

    def testPageJobScriptListView(self):
        """Test PageJobScriptListView"""
        # inst_req_only = self.make_instance(include_optional=False)
        # inst_req_and_optional = self.make_instance(include_optional=True)

if __name__ == '__main__':
    unittest.main()
