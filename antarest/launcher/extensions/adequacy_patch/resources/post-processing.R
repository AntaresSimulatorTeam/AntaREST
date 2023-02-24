library(AdequacyPatch)
library(antaresRead)
library(antaresEditObject)
library(yaml)
library(parallel)
library(data.table)
library(stringr)

opts <- setSimulationPath(".")

print(readLayout(opts = opts))

config <- read_yaml("user/adequacypatch/config.yml", fileEncoding = "UTF-8", text)

areas = setdiff(config$areas, config$exluded_areas)
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
					core_ahc = core_ahc,
                    calculate_mc_all = calculate_mc_all,
                    log_detail = TRUE)

areas <- read_yaml("user/adequacypatch/hourly-areas.yml", fileEncoding = "UTF-8", text)
links <- read_yaml("user/adequacypatch/hourly-links.yml", fileEncoding = "UTF-8", text)

remove_data <- function(path_prefix, data_type, data_list, include_id) {
    for (item in names(data_list)) {
        if (!data_list[[item]]) {
            item_data <- paste(c(path_prefix, data_type, item), collapse="/")
            cat(paste0("Removing from ", data_type, " ", item, " in ", path_prefix, "\n"))
            unlink(file.path(paste0(c(item_data, "values-hourly.txt"), collapse="/")))
            if (include_id) {
                unlink(file.path(paste0(c(item_data, "id-hourly.txt"), collapse="/")))
            }
            unlink(file.path(paste0(c(item_data, "details-hourly.txt"), collapse="/")))
            unlink(file.path(paste0(c(item_data, "details-res-hourly.txt"), collapse="/")))
            if (length(list.files(file.path(item_data))) == 0) {
                unlink(file.path(item_data))
            }
        }
    }
}

for (output in list.files("output")) {
    for (run_type in c("economy", "adequacy", "adequacy-draft")) {
        output_data <- paste(c("output", output, run_type), collapse="/")
        if (file.exists(output_data)) {
            # mc ind
            mc_data <- paste(c(output_data, "mc-ind"), collapse="/")
            if (!file.exists("user/adequacypatch/year-by-year-active")) {
                unlink(mc_data, recursive=TRUE)
            }
            else if (file.exists(mc_data)) {
                for (mc_year in list.files(file.path(mc_data))) {
                    remove_data(c(mc_data, mc_year), "areas", areas, FALSE)
                    remove_data(c(mc_data, mc_year), "links", links, FALSE)
                }
            }
            # mc all
#             mc_data <- paste(c(output_data, "mc-all"), collapse="/")
#             if (file.exists(mc_data)) {
#                 remove_data(mc_data, "areas", areas, TRUE)
#                 remove_data(mc_data, "links", links, TRUE)
#             }
        }
    }
}

cleanUpOutput(areas = config$areas)
