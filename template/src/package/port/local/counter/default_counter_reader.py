"""DefaultCounterReader: counter.json 을 읽는다. 파일이 없으면 0."""

from __future__ import annotations

from package.common import files
from package.model.counter.counter import Counter
from package.port.local.counter.counter_file import counter_file
from package.port.local.counter.counter_file_converter import CounterFileConverter
from package.port.local.counter.counter_reader import CounterReader


class DefaultCounterReader(CounterReader):
    def read(self) -> Counter:
        p = counter_file()
        return CounterFileConverter().to_data(files.read_json(p)) if p.exists() else Counter(0)
