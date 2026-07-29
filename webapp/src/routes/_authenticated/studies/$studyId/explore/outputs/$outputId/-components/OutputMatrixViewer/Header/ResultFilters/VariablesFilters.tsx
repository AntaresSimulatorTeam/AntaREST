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

import StringFE from "@/components/fieldEditors/StringFE";
import usePromise from "@/hooks/usePromise";
import useStudy from "@/routes/_authenticated/studies/$studyId/-hooks/useStudy";
import { getVariablesList } from "@/services/api/studies/outputs/variableViews";
import { Autocomplete } from "@mui/material";
import { useEffect, useMemo } from "react";
import { useTranslation } from "react-i18next";
import { useUnmount } from "react-use";
import useOutput from "../../../../-hooks/useOutput";
import useOutputContext from "../../../../-hooks/useOutputFilters";
import { isAreaOrDistrict } from "../../../../-utils";
import { isClusterDataType } from "../../utils";
import { getClusters, getVariables } from "./utils";

function VariablesFilters() {
  const study = useStudy();
  const output = useOutput();
  const { t } = useTranslation();
  const { item, dataType, variable, setVariable, clusterId, setClusterId } = useOutputContext();
  const showClusterField = isAreaOrDistrict(item) && isClusterDataType(dataType);

  const { data: variablesList } = usePromise(
    () => getVariablesList({ studyId: study.id, outputId: output.id }),
    {
      resetDataOnReload: true,
      deps: [study.id, output.id],
    },
  );

  const variableOptions = useMemo(() => {
    if (!variablesList) {
      return [];
    }
    return getVariables({ variablesList, item, dataType, clusterId });
  }, [clusterId, dataType, item, variablesList]);

  const clusterOptions = useMemo(() => {
    if (!variablesList || !showClusterField) {
      return [];
    }
    return getClusters(variablesList, dataType, item.id).map((cluster) => cluster.name);
  }, [variablesList, showClusterField, dataType, item.id]);

  // Select the first variable by default
  useEffect(() => {
    setVariable(variableOptions[0] || "");
  }, [variableOptions, setVariable]);

  // Select the first cluster by default
  useEffect(() => {
    setClusterId(clusterOptions[0] || "");
  }, [clusterOptions, setClusterId]);

  // Reset variable and clusterId on unmount
  useUnmount(() => {
    setVariable("");
    setClusterId("");
  });

  ////////////////////////////////////////////////////////////////
  // Utils
  ////////////////////////////////////////////////////////////////

  const getClusterFieldLabel = () => {
    switch (dataType) {
      case "details":
        return t("study.outputs.thermalCluster");
      case "details-res":
        return t("study.outputs.renewableCluster");
      case "details-STstorage":
        return t("study.outputs.shortTermStorage");
      default:
        return;
    }
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <>
      {showClusterField && (
        <Autocomplete
          options={clusterOptions}
          value={clusterId}
          onChange={(_event, newValue) => {
            setClusterId(newValue || "");
          }}
          disabled={clusterOptions.length === 0}
          noOptionsText={t("study.outputs.noClusters")}
          size="extra-small"
          renderInput={(params) => (
            <StringFE
              {...params}
              label={getClusterFieldLabel()}
              sx={{ minWidth: 200 }}
              size="extra-small"
            />
          )}
        />
      )}
      <Autocomplete
        options={variableOptions}
        value={variable}
        onChange={(_event, newValue) => {
          setVariable(newValue || "");
        }}
        disabled={variableOptions.length === 0}
        noOptionsText={t("study.outputs.noVariables")}
        size="extra-small"
        renderInput={(params) => (
          <StringFE
            {...params}
            label={t("study.outputs.variable")}
            sx={{ minWidth: 200 }}
            size="extra-small"
          />
        )}
      />
    </>
  );
}

export default VariablesFilters;
