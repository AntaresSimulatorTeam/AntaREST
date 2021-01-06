import json
import requests


def main(host: str = "http://localhost:8080"):
    res = requests.get(f"{host}/studies")

    if res.status_code != 200:
        print(f"Error to fetch studies list return code {res.status_code}")
        return

    studies = res.json()
    print(f"There are {len(studies)} studies to test")

    for study in studies:
        print(f"Test {study}...", end="\t")
        res = requests.get(f"{host}/studies/{study}?depth=-1")
        print(f"Success") if res.status_code == 200 else print("FAIL")


if __name__ == "__main__":
    main()
