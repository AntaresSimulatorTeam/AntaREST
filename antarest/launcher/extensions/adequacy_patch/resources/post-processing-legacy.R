library(AdequacyPatch)
library(antaresRead)
library(yaml)
library(parallel)

opts <- setSimulationPath(".")

print(readLayout(opts = opts))

config <- read_yaml("user/adequacypatch/config.yml", fileEncoding = "UTF-8", text)

run_adq(opts = opts,
					areas = config$areas,
					virtual_areas = config$areas,
					mcYears = config$mcYears,
					antaresfbzone = config$antaresfbzone,
					ext = NULL,
					nbcl = config$nbcore, thresholdFilter = config$thresholdFilter,
					core_ahc = config$core_ahc)

areas <- read_yaml("user/adequacypatch/hourly-areas.yml", fileEncoding = "UTF-8", text)
for (area in names(areas)) {
  if (!areas[[area]]) {
    print(area)
  }
}
