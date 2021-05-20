from abc import ABC, abstractmethod


class HeadWriter(ABC):
    @abstractmethod
    def build(self, var: int, end: int, start: int = 1) -> str:
        raise NotImplementedError()


class AreaHeadWriter(HeadWriter):
    def __init__(self, area: str, freq: str):
        self.head = f"""{area.upper()}\tarea\t{area.lower()}\t{freq}
\tVARIABLES\tBEGIN\tEND
"""

    def build(self, var: int, end: int, start: int = 1) -> str:
        return self.head + f"\t{var}\t{start}\t{end}\n\n"


class LinkHeadWriter(HeadWriter):
    def __init__(self, src: str, dest: str, freq: str):
        self.head = f"""{src.upper()}\tlink\tva\t{freq}
{dest.upper()}\tVARIABLES\tBEGIN\tEND
"""

    def build(self, var: int, end: int, start: int = 1) -> str:
        return self.head + f"\t{var}\t{start}\t{end}\n\n"
