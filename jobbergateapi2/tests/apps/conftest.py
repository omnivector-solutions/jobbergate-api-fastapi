"""
Pytest helpers to use in all apps
"""
from typing import List

import sqlalchemy
from pydantic import BaseModel
from pytest import fixture

from jobbergateapi2.storage import database


async def insert_objects(objects: List[BaseModel], table: sqlalchemy.Table):
    """
    Perform a database insertion for the objects passed as the argument, into
    the specified table
    """
    ModelType = type(objects[0])
    await database.execute_many(query=table.insert(), values=[obj.dict() for obj in objects])
    fetched = await database.fetch_all(table.select())
    return [ModelType.parse_obj(o) for o in fetched]


@fixture
def user_data():
    """
    Default user data for testing
    """
    return {
        "email": "user1@email.com",
        "full_name": "username",
        "password": "supersecret123456",
        "principals": "role:admin"
    }


@fixture
def application_data():
    """
    Default application data for testing.
    """
    return {
        "application_name": "test_name",
        "application_file": "the\nfile",
        "application_config": "the configuration is here",
    }


@fixture
def job_script_data():
    """
    Default job_script data for testing.
    """
    return {
        "job_script_name": "test_name",
        "job_script_data_as_string": "the\nfile",
        "job_script_owner_id": 1,
        "application_id": 1,
    }
