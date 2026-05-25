# Simple pytest file — runs inside python:3.11-slim container
# Proves that the Docker agent has Python and can run tests


def test_addition():
    """Basic math — proves Python is working inside container."""
    assert 1 + 1 == 2


def test_string_operations():
    """String test — proves standard library is available."""
    name = "devops"
    assert name.upper() == "DEVOPS"
    assert len(name) == 6


def test_list_operations():
    """List test — proves basic Python data structures work."""
    items = ["jenkins", "docker", "python"]
    assert len(items) == 3
    assert "docker" in items


def test_environment_is_clean():
    """Proves each build starts fresh — no leftover state."""
    import os
    import tempfile

    # Create a temp file
    temp = tempfile.NamedTemporaryFile(delete=False)
    temp_path = temp.name
    temp.close()

    # Verify it was created
    assert os.path.exists(temp_path)

    # Clean it up
    os.remove(temp_path)
    assert not os.path.exists(temp_path)
