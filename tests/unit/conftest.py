#!/usr/bin/env python3
"""
conftest.py --- shared fixtures for unit tests

Contains:
    triple_factory fixture
"""

import pytest

from extract.schema import Triple
from tests.unit.factories import make_triple


@pytest.fixture
def triple_factory():
    """Provides the make_triple factory as a fixture.

    Returns:
        factory: The make_triple function.
    """
    return make_triple
