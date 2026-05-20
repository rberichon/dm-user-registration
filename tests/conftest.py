import pytest
from fastapi.testclient import TestClient

import app.main as main_module
from app.main import app


@pytest.fixture
def client():
    main_module.user_table.clear()
    main_module.code_table.clear()
    yield TestClient(app)
