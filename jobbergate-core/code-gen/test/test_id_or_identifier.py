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

from openapi_client.models.id_or_identifier import IdOrIdentifier  # noqa: E501

class TestIdOrIdentifier(unittest.TestCase):
    """IdOrIdentifier unit test stubs"""

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def make_instance(self, include_optional) -> IdOrIdentifier:
        """Test IdOrIdentifier
            include_option is a boolean, when False only required
            params are included, when True both required and
            optional params are included """
        # uncomment below to create an instance of `IdOrIdentifier`
        """
        model = IdOrIdentifier()  # noqa: E501
        if include_optional:
            return IdOrIdentifier(
            )
        else:
            return IdOrIdentifier(
        )
        """

    def testIdOrIdentifier(self):
        """Test IdOrIdentifier"""
        # inst_req_only = self.make_instance(include_optional=False)
        # inst_req_and_optional = self.make_instance(include_optional=True)

if __name__ == '__main__':
    unittest.main()
