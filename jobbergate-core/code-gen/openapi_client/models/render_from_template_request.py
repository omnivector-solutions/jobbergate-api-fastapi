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


from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, StrictStr, conlist

class RenderFromTemplateRequest(BaseModel):
    """
    Request model for creating a JobScript entry from a template.  # noqa: E501
    """
    template_output_name_mapping: Any = Field(..., description="A mapping of template names to file names. The first element is the entrypoint, the others are optional support files.")
    sbatch_params: Optional[conlist(StrictStr)] = Field(None, description="SBATCH parameters to inject into the job_script")
    param_dict: Dict[str, Any] = Field(..., description="Parameters to use when rendering the job_script jinja2 template")
    __properties = ["template_output_name_mapping", "sbatch_params", "param_dict"]

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
    def from_json(cls, json_str: str) -> RenderFromTemplateRequest:
        """Create an instance of RenderFromTemplateRequest from a JSON string"""
        return cls.from_dict(json.loads(json_str))

    def to_dict(self):
        """Returns the dictionary representation of the model using alias"""
        _dict = self.dict(by_alias=True,
                          exclude={
                          },
                          exclude_none=True)
        return _dict

    @classmethod
    def from_dict(cls, obj: dict) -> RenderFromTemplateRequest:
        """Create an instance of RenderFromTemplateRequest from a dict"""
        if obj is None:
            return None

        if not isinstance(obj, dict):
            return RenderFromTemplateRequest.parse_obj(obj)

        _obj = RenderFromTemplateRequest.parse_obj({
            "sbatch_params": obj.get("sbatch_params"),
            "param_dict": obj.get("param_dict")
        })
        return _obj


