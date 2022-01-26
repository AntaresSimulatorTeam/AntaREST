library(AdequacyPatch)
library(antaresRead)
library(yaml)

opts <- setSimulationPath(".")

print(readLayout(opts = opts))

# config <- read_yaml("user/adequacypatch/config.yaml", fileEncoding = "UTF-8", text)
#
# areas <- c("fr", "at", "be", "de", "nl", "es", "ukgb", "ch", "ie", "itn", "model_description_fb")
# virtual_areas = getAreas(select = "_", regexpSelect = TRUE,
#                          exclude = c("model_description_fb"), regexpExclude = FALSE)
#
#
# run_adq(opts = opts,
# 					areas = areas,
# 					virtual_areas = virtual_areas,
# 					mcYears = "all",
# 					antaresfbzone = "model_description_fb",
# 					ext = 'adq',
# 					nbcl = 8, thresholdFilter = 100)