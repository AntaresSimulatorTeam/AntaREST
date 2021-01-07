import hashlib
import json
from pathlib import Path
from typing import Optional

import requests

OKGREEN = "\033[92m"
FAIL = "\033[91m"
ENDC = "\033[0m"


def export(host: str, study: str) -> Optional[bytes]:
    res = requests.get(f"{host}/studies/{study}/export?compact")
    if res.status_code == 200:
        print(f"{OKGREEN}EXPORT SUCCESS{ENDC}", end=" | ")
        return res.content
    else:
        print(f"{FAIL}FAIL to EXPORT{ENDC}")
        return None


def importation(host: str, study: bytes) -> Optional[str]:
    headers = {"Content-Length": str(len(study))}
    res = requests.post(
        f"{host}/studies", headers=headers, files={"study": study}
    )
    if res.status_code == 201:
        url: str = res.json()
        print(f"{OKGREEN}IMPORT SUCCESS{ENDC}", end=" | ")
        return url[len("/studies/") :]
    else:
        print(f"{FAIL}FAIL to EXPORT{ENDC}")
        return None


def compare(origin: Path, copy: Path):
    def hash(file: Path) -> str:
        return hashlib.md5(open(file, "rb").read()).hexdigest()

    if origin.is_file():
        if not copy.is_file():
            print(f"{FAIL}file {origin} not present in copy{ENDC}")

    else:
        if not copy.is_dir():
            print(f"{FAIL}file {origin} not present in copy{ENDC}")
        for child in origin.iterdir():
            compare(child, copy / child.name)


def main(path: Path, host: str = "http://localhost:8080"):
    res = requests.get(f"{host}/studies")

    if res.status_code != 200:
        print(
            f"{FAIL}Error to fetch studies list return code {res.status_code}{ENDC}"
        )
        return

    studies = res.json()
    print(f"There are {len(studies)} studies to test")

    for study in studies:
        print(f"{study:>80}", end="\t")

        data = export(host, study)
        if data:
            uuid = importation(host, data)
            print(uuid)
            if uuid:
                compare(origin=path / study, copy=path / uuid)
                print(f"{OKGREEN}COMPARE SUCCESS{ENDC}")
        return


if __name__ == "__main__":
    path = Path("/Volumes/Crucial X8/antares/Antares_Simulator_Examples")
    main(path=path)
