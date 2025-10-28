from typing import TypedDict


class Organization(TypedDict):
    id: str
    name: str


class Membership(TypedDict):
    organization_id: str
    user_id: str
    organization: Organization


class ApiKey(TypedDict):
    id: str
    key_name: str
    masked_key: str
    full_key: str
    created_at: str