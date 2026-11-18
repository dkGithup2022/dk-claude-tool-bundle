import pytest


@pytest.fixture(autouse=True)
def package_home(tmp_path, monkeypatch):
    """모든 시험은 임시 폴더를 실행 데이터 폴더로 쓴다."""
    home = tmp_path / ".package"
    monkeypatch.setenv("PACKAGE_HOME", str(home))
    return home
