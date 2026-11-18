from package.model.counter.counter import Counter
from package.port.local.counter.default_counter_reader import DefaultCounterReader
from package.port.local.counter.default_counter_writer import DefaultCounterWriter


def test_should_read_zero_when_no_file_and_read_back_saved_counter():
    assert DefaultCounterReader().read() == Counter(0)
    DefaultCounterWriter().save(Counter(3))
    assert DefaultCounterReader().read() == Counter(3)
