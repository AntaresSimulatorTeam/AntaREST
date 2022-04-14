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
nbcore = config$nbcore

run_adq(opts = opts,
					areas = areas,
					virtual_areas = areas,
					mcYears = mcYears,
					antaresfbzone = antaresfbzone,
					ext = extension,
					nbcl = nbcore, thresholdFilter = thresholdFilter,
					core_ahc = core_ahc)

areas <- read_yaml("user/adequacypatch/hourly-areas.yml", fileEncoding = "UTF-8", text)

for (output in list.files("output")) {
    for (run_type in c("economy", "adequacy", "adequacy-draft")) {
        output_data <- paste(c("output", output, run_type), collapse="/")
            if (file.exists(output_data)) {
                # mc ind
                mc_data <- paste(c(output_data, "mc-ind"), collapse="/")
                if (file.exists(mc_data)) {
                    for (mc_year in list.files(file.path(mc_data))) {
                        for (area in names(areas)) {
                            if (!areas[[area]]) {
                                area_data <- paste(c(mc_data, mc_year, "areas", area), collapse="/")
                                cat(paste0("Removing area ", area, " for year ", mc_year))
                                unlink(file.path(paste0(area_data, "values-hourly.txt", collapse="/")))
                                unlink(file.path(paste0(area_data, "details-hourly.txt", collapse="/")))
                                if (length(list.files(file.path(area_data))) == 0) {
                                    unlink(file.path(area_data))
                                }
                            }
                        }
                    }
                }
                # mc all
                mc_data <- paste(c(output_data, "mc-all"), collapse="/")
                if (file.exists(mc_data)) {
                for (area in names(areas)) {
                    if (!areas[[area]]) {
                        area_data <- paste(c(mc_data, "areas", area), collapse="/")
                        cat(paste0("Removing area ", area, " for year ", mc_year))
                        unlink(file.path(paste0(area_data, "values-hourly.txt", collapse="/")))
                        unlink(file.path(paste0(area_data, "id-hourly.txt", collapse="/")))
                        unlink(file.path(paste0(area_data, "details-hourly.txt", collapse="/")))
                        if (length(list.files(file.path(area_data))) == 0) {
                            unlink(file.path(area_data))
                        }
                    }
                }
            }
        }
    }
}

