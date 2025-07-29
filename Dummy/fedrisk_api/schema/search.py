from datetime import datetime
from typing import Dict, List

from pydantic import BaseModel


class DisplayObjectReference(BaseModel):
    id: str
    name: str
    description: str

    class Config:
        extra = "allow"


class ObjectSearchResults(BaseModel):
    search_string: str
    object_type: str
    search_results: List[DisplayObjectReference]
    total_objects: int


class SearchResults(BaseModel):
    search_string: str
    search_timestamp: datetime = None
    object_types: List[str]
    results: Dict[str, ObjectSearchResults]

    class Config:  # This is inside UnionChild, do not place it outside.
        schema_extra = {
            "example": {  # Mandatory field, this holds your example. Define Your Field from here.
                "search_string": "*work*",
                "search_timestamp": "2022-06-02T12:37:30.334947",
                "object_types": ["framework", "control"],
                "results": {
                    "framework": {
                        "total_objects": 10,
                        "search_string": "*work*",
                        "object_type": "framework",
                        "search_results": [
                            {
                                "id": "1",
                                "name": "Framework 1",
                                "description": "Demonstration Framework",
                            },
                            {
                                "id": "2",
                                "name": "Framework 2",
                                "description": "Demonstration Framework",
                            },
                        ],
                    },
                    "control": {
                        "total_objects": 0,
                        "search_string": "*work*",
                        "object_type": "control",
                        "search_results": [],
                    },
                },
            }
        }
