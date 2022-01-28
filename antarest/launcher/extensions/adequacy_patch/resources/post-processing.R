library(AdequacyPatch)
library(antaresRead)
library(yaml)

opts <- setSimulationPath(".")

print(readLayout(opts = opts))

config <- read_yaml("user/adequacypatch/config.yml", fileEncoding = "UTF-8", text)

run_adq(opts = opts,
					areas = config$areas,
					virtual_areas = config$areas,
					mcYears = config$mcYears,
					antaresfbzone = config$antaresfbzone,
					ext = NULL,
					nbcl = 1, thresholdFilter = config$thresholdFilter,
					core_ahc = config$core_ahc,
                    calculate_mc_all = config$calculate_mc_all,
                    log_detail = TRUE)