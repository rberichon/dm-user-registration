import pytest
from fastapi.testclient import TestClient

import app.api.v1.routes.users as users_route
from app.main import app


@pytest.fixture
def client():
    users_route.user_table.clear()
    users_route.code_table.clear()
    yield TestClient(app)
