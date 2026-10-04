"""Basic package import and version test."""

import learning_app


def test_package_version() -> None:
    """Verify package import and version string."""
    assert learning_app.__version__ == "0.1.0"
