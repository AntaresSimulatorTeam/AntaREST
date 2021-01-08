import hashlib
import json
import shutil
from pathlib import Path
from typing import Optional

import requests

OKGREEN = "\033[92m"
FAIL = "\033[91m"
ENDC = "\033[0m"


def export(host: str, study: str) -> Optional[bytes]:
    """
    Send exportation request.

    Args:
        host: server url
        study: study id

    Returns: zip file if request success

    """
    res = requests.get(f"{host}/studies/{study}/export?compact")
    if res.status_code == 200:
        print(f"{OKGREEN}EXPORT SUCCESS{ENDC}", end=" | ")
        return res.content
    else:
        print(f"{FAIL}FAIL to EXPORT{ENDC}")
        return None


def importation(host: str, study: bytes) -> Optional[str]:
    """
    Send importation request.

    Args:
        host: url server
        study: zip file

    Returns: study id if request request

    """
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


def compare(origin: Path, copy: Path) -> bool:
    """
    Compare file by file to folder.

    Args:
        origin: origin folder
        copy: copy folder to compare

    Returns: True if all files and folders are same

    """
    if origin.is_file():
        if not copy.is_file():
            print(f"{FAIL}file {origin} not present in copy{ENDC}")
            return False
        return True

    else:
        if not copy.is_dir():
            print(f"{FAIL}file {origin} not present in copy{ENDC}")
            return False
        return all(
            compare(child, copy / child.name) for child in origin.iterdir()
        )


def main(path: Path, host: str) -> None:
    res = requests.get(f"{host}/studies")

    if res.status_code != 200:
        print(
            f"{FAIL}Error to fetch studies list return code {res.status_code}{ENDC}"
        )
        return

    studies = res.json()
    print(f"There are {len(studies)} studies to test")

    for study in studies:
        print(f"{study[:3]}", end="\t")

        data = export(host, study)
        if data:
            uuid = importation(host, data)
            if uuid:
                res = compare(origin=path / study, copy=path / uuid)
                print(f"{OKGREEN}COMPARE SUCCESS{ENDC}") if res else print("")
                shutil.rmtree(path / uuid)


if __name__ == "__main__":
    path = Path("/Volumes/Crucial X8/antares/Antares_Simulator_Examples")
    host = "http://localhost:8080"
    main(path=path, host=host)
