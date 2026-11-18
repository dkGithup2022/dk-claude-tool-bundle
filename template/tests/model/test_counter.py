from package.model.counter.counter import Counter


def test_should_return_new_counter_increased_by_one():
    c = Counter(7)
    assert c.up() == Counter(8) and c == Counter(7)
