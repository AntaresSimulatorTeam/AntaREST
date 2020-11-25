import pytest

from api_iso_antares.web.request_handler import (
    RequestHandlerParameters,
    RequestHandler,
    Benchmark,
)


def launch(
    request_handler: RequestHandler, url: str, repeat: int
) -> Benchmark:
    url = url[len("/studies/") :]
    main = Benchmark()
    print(url, end=" ")
    for _ in range(0, repeat):
        _, bench = request_handler.get(
            route=url, parameters=RequestHandlerParameters()
        )

        main.parse += bench.parse / repeat
        main.url += bench.url / repeat
        main.write += bench.write / repeat
        print("*", end=" ")
    print("")
    return main


@pytest.mark.unit_test
def test_sta_mini_output(request_handler: RequestHandler) -> None:

    urls = [
        "/studies/STA-mini/settings/generaldata",  # big .ini
        "/studies/STA-mini/input/hydro/series/de/mod.txt",  # file
        "/studies/STA-mini/input/areas/sets",  # little .ini
        "/studies/STA-mini",  # all study
        "/studies/STA-mini/input/hydro",  # sub study
    ]
    benchs = {
        url: launch(request_handler=request_handler, url=url, repeat=10)
        for url in urls
    }
    print(benchs)
