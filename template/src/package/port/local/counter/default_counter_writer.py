"""DefaultCounterWriter: counter.json 을 쓴다."""

from __future__ import annotations

from package.common import files
from package.model.counter.counter import Counter
from package.port.local.counter.counter_file import counter_file
from package.port.local.counter.counter_file_converter import CounterFileConverter
from package.port.local.counter.counter_writer import CounterWriter


class DefaultCounterWriter(CounterWriter):
    def save(self, counter: Counter) -> None:
        files.write_json(counter_file(), CounterFileConverter().to_file(counter))
