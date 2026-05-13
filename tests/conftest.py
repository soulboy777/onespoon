"""测试配置和 fixtures"""

import pytest

from src.core.config import reset_config


@pytest.fixture(autouse=True)
def reset_config_between_tests() -> None:
    """每个测试前重置配置"""
    reset_config()
    yield
    reset_config()
