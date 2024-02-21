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

from openapi_client.models.job_submission_create_request import JobSubmissionCreateRequest  # noqa: E501

class TestJobSubmissionCreateRequest(unittest.TestCase):
    """JobSubmissionCreateRequest unit test stubs"""

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def make_instance(self, include_optional) -> JobSubmissionCreateRequest:
        """Test JobSubmissionCreateRequest
            include_option is a boolean, when False only required
            params are included, when True both required and
            optional params are included """
        # uncomment below to create an instance of `JobSubmissionCreateRequest`
        """
        model = JobSubmissionCreateRequest()  # noqa: E501
        if include_optional:
            return JobSubmissionCreateRequest(
                name = 'test-job-submission-77',
                description = 'Submission for the Foo job on sample 99 using the bar variant',
                job_script_id = 71,
                slurm_job_id = 1883,
                execution_directory = '/home/someuser/job-data/test-77',
                client_id = 'mega-cluster-1',
                execution_parameters = {name=job-submission-name, comment=I am a comment}
            )
        else:
            return JobSubmissionCreateRequest(
                name = 'test-job-submission-77',
                job_script_id = 71,
        )
        """

    def testJobSubmissionCreateRequest(self):
        """Test JobSubmissionCreateRequest"""
        # inst_req_only = self.make_instance(include_optional=False)
        # inst_req_and_optional = self.make_instance(include_optional=True)

if __name__ == '__main__':
    unittest.main()
