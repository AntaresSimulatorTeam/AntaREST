/**
 * Copyright (c) 2026, RTE (https://www.rte-france.com)
 *
 * See AUTHORS.txt
 *
 * This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/.
 *
 * SPDX-License-Identifier: MPL-2.0
 *
 * This file is part of the Antares project.
 */

/** Illustrative paths only. This design preview does not read the output filesystem. */
export const sampleFiles = [
  "gems-views/electricity/annual/generation.csv",
  "gems-views/electricity/hourly/generation.csv",
  "gems-views/electricity/annual/marginal-prices.csv",
  "gems-views/storage/hourly/state-of-charge.parquet",
  "gems-views/hydrogen/annual/production-by-technology-and-region.csv",
  "simulation-tables/components.parquet",
  "simulation-tables/constraints.parquet",
  "metadata/execution-info.json",
  "logs/simulation.log",
  "demo/example-output.csv",
].map((path) => {
  const separator = path.lastIndexOf("/");
  const name = path.slice(separator + 1);

  return {
    path,
    name,
    folder: path.slice(0, separator),
    extension: name.slice(name.lastIndexOf(".") + 1).toUpperCase(),
    demo: path === "demo/example-output.csv",
  };
});

/** Deliberately synthetic data for exercising the preview's download interaction. */
export const demoCsv = "example,scenario,value\nillustrative_data,0,12\nillustrative_data,1,18\n";
