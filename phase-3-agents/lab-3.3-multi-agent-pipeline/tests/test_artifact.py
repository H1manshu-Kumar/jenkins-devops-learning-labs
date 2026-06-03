from pathlib import Path


def test_artifact_exists():
    assert Path("build/app.txt").exists()


def test_artifact_content():
    content = Path("build/app.txt").read_text()
    assert "Application Build Artifact" in content
