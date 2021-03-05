from pathlib import Path

import pkg_resources
import pytest
import atexit
# noinspection PyProtectedMember
from barcode_reader._zxing import _executors


@pytest.fixture
def resources():
    yield Path(pkg_resources.resource_filename("tests", "resources"))


@pytest.fixture(scope="session", autouse=True)
def _handle_executors():
    """
    This fixture ensure that Zxing executors are shutdown at the end of tests execution which is necessary for
    pytest-cov to get results from the _zxing module parts executed in subprocesses
    """
    yield
    _executors.shutdown()
