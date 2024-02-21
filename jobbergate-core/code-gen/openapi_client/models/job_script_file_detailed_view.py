# coding: utf-8

"""
    Jobbergate-API

    No description provided (generated by Openapi Generator https://github.com/openapitools/openapi-generator)

    The version of the OpenAPI document: 4.3.0a1
    Contact: info@omnivector.solutions
    Generated by OpenAPI Generator (https://openapi-generator.tech)

    Do not edit the class manually.
"""  # noqa: E501


from __future__ import annotations
import pprint
import re  # noqa: F401
import json

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, conint, constr
from openapi_client.models.file_type import FileType

class JobScriptFileDetailedView(BaseModel):
    """
    Model for the job_script_files field of the JobScript resource.  # noqa: E501
    """
    parent_id: conint(strict=True, ge=0) = Field(..., description="The unique database identifier for the parent of this instance")
    filename: constr(strict=True, max_length=255) = Field(..., description="The name of the file")
    file_type: FileType = Field(..., description="The type of the file")
    created_at: Optional[datetime] = Field(None, description="The timestamp for when the instance was created")
    updated_at: Optional[datetime] = Field(None, description="The timestamp for when the instance was last updated")
    __properties = ["parent_id", "filename", "file_type", "created_at", "updated_at"]

    class Config:
        """Pydantic configuration"""
        allow_population_by_field_name = True
        validate_assignment = True

    def to_str(self) -> str:
        """Returns the string representation of the model using alias"""
        return pprint.pformat(self.dict(by_alias=True))

    def to_json(self) -> str:
        """Returns the JSON representation of the model using alias"""
        return json.dumps(self.to_dict())

    @classmethod
    def from_json(cls, json_str: str) -> JobScriptFileDetailedView:
        """Create an instance of JobScriptFileDetailedView from a JSON string"""
        return cls.from_dict(json.loads(json_str))

    def to_dict(self):
        """Returns the dictionary representation of the model using alias"""
        _dict = self.dict(by_alias=True,
                          exclude={
                          },
                          exclude_none=True)
        return _dict

    @classmethod
    def from_dict(cls, obj: dict) -> JobScriptFileDetailedView:
        """Create an instance of JobScriptFileDetailedView from a dict"""
        if obj is None:
            return None

        if not isinstance(obj, dict):
            return JobScriptFileDetailedView.parse_obj(obj)

        _obj = JobScriptFileDetailedView.parse_obj({
            "parent_id": obj.get("parent_id"),
            "filename": obj.get("filename"),
            "file_type": obj.get("file_type"),
            "created_at": obj.get("created_at"),
            "updated_at": obj.get("updated_at")
        })
        return _obj


