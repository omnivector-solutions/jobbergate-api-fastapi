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

from openapi_client.models.page_pending_job_submission import PagePendingJobSubmission  # noqa: E501

class TestPagePendingJobSubmission(unittest.TestCase):
    """PagePendingJobSubmission unit test stubs"""

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def make_instance(self, include_optional) -> PagePendingJobSubmission:
        """Test PagePendingJobSubmission
            include_option is a boolean, when False only required
            params are included, when True both required and
            optional params are included """
        # uncomment below to create an instance of `PagePendingJobSubmission`
        """
        model = PagePendingJobSubmission()  # noqa: E501
        if include_optional:
            return PagePendingJobSubmission(
                items = [
                    openapi_client.models.pending_job_submission.PendingJobSubmission(
                        id = 101, 
                        name = 'test-job-submission-77', 
                        owner_email = 'tucker@omnivector.solutions', 
                        execution_directory = '/home/someuser/job-data/test-77', 
                        execution_parameters = {name=job-submission-name, comment=I am a comment}, 
                        job_script = openapi_client.models.job_script_detailed_view.JobScriptDetailedView(
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
                            cloned_from_id = 101, 
                            files = [
                                openapi_client.models.job_script_file_detailed_view.JobScriptFileDetailedView(
                                    parent_id = 101, 
                                    filename = 'job-script.py', 
                                    file_type = ENTRYPOINT, 
                                    created_at = '2023-08-18T13:55:37.172285', 
                                    updated_at = '2023-08-18T13:55:37.172285', )
                                ], ), )
                    ],
                total = 0.0,
                page = 1.0,
                size = 1.0,
                pages = 0.0
            )
        else:
            return PagePendingJobSubmission(
                items = [
                    openapi_client.models.pending_job_submission.PendingJobSubmission(
                        id = 101, 
                        name = 'test-job-submission-77', 
                        owner_email = 'tucker@omnivector.solutions', 
                        execution_directory = '/home/someuser/job-data/test-77', 
                        execution_parameters = {name=job-submission-name, comment=I am a comment}, 
                        job_script = openapi_client.models.job_script_detailed_view.JobScriptDetailedView(
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
                            cloned_from_id = 101, 
                            files = [
                                openapi_client.models.job_script_file_detailed_view.JobScriptFileDetailedView(
                                    parent_id = 101, 
                                    filename = 'job-script.py', 
                                    file_type = ENTRYPOINT, 
                                    created_at = '2023-08-18T13:55:37.172285', 
                                    updated_at = '2023-08-18T13:55:37.172285', )
                                ], ), )
                    ],
                total = 0.0,
        )
        """

    def testPagePendingJobSubmission(self):
        """Test PagePendingJobSubmission"""
        # inst_req_only = self.make_instance(include_optional=False)
        # inst_req_and_optional = self.make_instance(include_optional=True)

if __name__ == '__main__':
    unittest.main()
