import pytest


class TestSomething:
    @pytest.fixture
    def a(self) -> int:
        return 1

    @pytest.fixture
    def b(self) -> int:
        return 2

    def test_a_plus_b(self, a: int, b: int) -> None:
        assert a + b == 3
