library(AdequacyPatch)
library(antaresRead)

opts <- setSimulationPath("myoutputstudy")

areas <- c("fr", "at", "be", "de", "nl", "es", "ukgb", "ch", "ie", "itn", "model_description_fb")
virtual_areas = getAreas(select = "_", regexpSelect = TRUE,
                         exclude = c("model_description_fb"), regexpExclude = FALSE)


run_adq(opts = opts,
					areas = areas,
					virtual_areas = virtual_areas,
					mcYears = "all",
					antaresfbzone = "model_description_fb",
					ext = 'adq',
					nbcl = 8, thresholdFilter = 100)