from core_features_1_100 import Core100, FEATURES


def test_permanent_numbering():
    assert len(FEATURES) == 100
    assert [f.number for f in FEATURES] == list(range(1, 101))
    assert all(f.kind == "CORE" for f in FEATURES if f.number % 2)
    assert all(f.kind == "OPTIONAL/NEW FEATURE" for f in FEATURES if f.number % 2 == 0)


def test_core_commands():
    jarvis = Core100()
    assert "Core commands" in jarvis.handle("help")
    assert "JARVIS Core" in jarvis.handle("status")
    assert "PASS" in jarvis.handle("self test")
    assert jarvis.handle("calculate 2 + 2 * 3") == "2 + 2 * 3 = 8"


if __name__ == "__main__":
    test_permanent_numbering()
    test_core_commands()
    print("JARVIS Core 1-100 smoke tests: PASS")
