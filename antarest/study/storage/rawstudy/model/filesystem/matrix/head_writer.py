from abc import ABC, abstractmethod


class HeadWriter(ABC):
    """
    Abstract head output matrix builder.
    """

    @abstractmethod
    def build(self, var: int, end: int, start: int = 1) -> str:
        """
        Build matrix header.
        Args:
            var: number of variables
            end: time horizon end
            start: time horizon start

        Returns: string header ready to save

        """
        raise NotImplementedError()


class AreaHeadWriter(HeadWriter):
    """
    Implementation for area head matrix.
    """

    def __init__(self, area: str, freq: str):
        self.head = f"""{area.upper()}\tarea\t{area.lower()}\t{freq}
\tVARIABLES\tBEGIN\tEND
"""

    def build(self, var: int, end: int, start: int = 1) -> str:
        return self.head + f"\t{var}\t{start}\t{end}\n\n"


class LinkHeadWriter(HeadWriter):
    """
    Implementation for link head matrix
    """

    def __init__(self, src: str, dest: str, freq: str):
        self.head = f"""{src.upper()}\tlink\tva\t{freq}
{dest.upper()}\tVARIABLES\tBEGIN\tEND
"""

    def build(self, var: int, end: int, start: int = 1) -> str:
        return self.head + f"\t{var}\t{start}\t{end}\n\n"
