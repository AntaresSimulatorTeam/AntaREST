import sys
import time
import random


def main() -> int:
    time.sleep(10)
    return random.randint(0, 1)


if __name__ == "__main__":
    sys.exit(main())
