from antarest.storage.model import Patch


class PatchService:
    def get(self) -> Patch:
        pass

    def save_simulator(self, sim: str):
        pass

    def save_ouput(self, out: str, ref: str):
        pass

    def save_area(self, area: str, country: str):
        pass
