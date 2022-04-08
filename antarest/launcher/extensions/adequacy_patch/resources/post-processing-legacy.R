library(AdequacyPatch)
library(antaresRead)
library(yaml)
library(parallel)

opts <- setSimulationPath(".")

print(readLayout(opts = opts))

config <- read_yaml("user/adequacypatch/config.yml", fileEncoding = "UTF-8", text)
areas = config$areas
virutal_areas = config$areas
mcYears = config$mcYears
antaresfbzone = config$antaresfbzone
thresholdFilter = config$thresholdFilter
core_ahc = config$core_ahc
calculate_mc_all = config$calculate_mc_all
extension = config$extension

run_adq(opts = opts,
					areas = areas,
					virtual_areas = areas,
					mcYears = mcYears,
					antaresfbzone = antaresfbzone,
					ext = extension,
					nbcl = 12, thresholdFilter = thresholdFilter,
					core_ahc = core_ahc)

areas <- read_yaml("user/adequacypatch/hourly-areas.yml", fileEncoding = "UTF-8", text)
for (area in names(areas)) {
  if (!areas[[area]]) {
    print(area)
  }
}
