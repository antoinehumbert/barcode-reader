from pathlib import Path

import pkg_resources
import pytest


@pytest.fixture
def resources():
    yield Path(pkg_resources.resource_filename("tests", "resources"))
