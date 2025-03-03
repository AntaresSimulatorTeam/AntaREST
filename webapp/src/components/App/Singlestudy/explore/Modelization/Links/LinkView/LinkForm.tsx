/**
 * Copyright (c) 2025, RTE (https://www.rte-france.com)
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

import { Box } from "@mui/material";
import type { AxiosError } from "axios";
import { useMemo } from "react";
import { useTranslation } from "react-i18next";
import { editStudy } from "../../../../../../../services/api/study";
import useEnqueueErrorSnackbar from "../../../../../../../hooks/useEnqueueErrorSnackbar";
import Fieldset from "../../../../../../common/Fieldset";
import type { AutoSubmitHandler } from "../../../../../../common/Form/types";
import { getLinkPath, type LinkFields } from "./utils";
import SwitchFE from "../../../../../../common/fieldEditors/SwitchFE";
import type { LinkElement, StudyMetadata } from "../../../../../../../types/types";
import SelectFE from "../../../../../../common/fieldEditors/SelectFE";
import LinkMatrixView from "./LinkMatrixView";
import OutputFilters from "../../../common/OutputFilters";
import { useFormContextPlus } from "../../../../../../common/Form";
import Matrix from "../../../../../../common/Matrix";

interface Props {
  link: LinkElement;
  study: StudyMetadata;
}

function LinkForm(props: Props) {
  const { study, link } = props;
  const studyId = study.id;
  const isTabMatrix = useMemo((): boolean => {
    let version = 0;
    try {
      version = parseInt(study.version, 10);
    } catch {
      version = 0;
    }
    return version >= 820;
  }, [study]);

  const { area1, area2 } = link;
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();
  const [t] = useTranslation();
  const path = useMemo(() => {
    return getLinkPath(area1, area2);
  }, [area1, area2]);

  const {
    control,
    formState: { defaultValues },
  } = useFormContextPlus<LinkFields>();

  const optionTransCap = ["infinite", "ignore", "enabled"].map((item) => ({
    label: t(`study.modelization.links.transmissionCapa.${item}`),
    value: item.toLowerCase(),
  }));

  const optionType = ["ac", "dc", "gaz", "virt", "other"].map((item) => ({
    label: t(`study.modelization.links.type.${item}`),
    value: item.toLowerCase(),
  }));

  const columnsNames = [
    t("study.modelization.links.matrix.columns.transCapaDirect"),
    t("study.modelization.links.matrix.columns.transCapaIndirect"),
    `${t("study.modelization.links.matrix.columns.hurdleCostsDirect")} (${area1}->${area2})`,
    `${t("study.modelization.links.matrix.columns.hurdleCostsIndirect")} (${area2}->${area1})`,
    t("study.modelization.links.matrix.columns.impedances"),
    t("study.modelization.links.matrix.columns.loopFlow"),
    t("study.modelization.links.matrix.columns.pShiftMin"),
    t("study.modelization.links.matrix.columns.pShiftMax"),
  ];

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const handleAutoSubmit = async (path: string, data: any) => {
    try {
      await editStudy(data, studyId, path);
    } catch (error) {
      enqueueErrorSnackbar(t("study.error.updateUI"), error as AxiosError);
    }
  };

  const handleTypeAutoSubmit: AutoSubmitHandler = (value) => {
    const defaultFilterSynthesis = defaultValues?.filterSynthesis
      ? (defaultValues?.filterSynthesis as string[]).filter((elm) => elm !== "")
      : [];
    const defaultFilterByYear = defaultValues?.filterByYear
      ? (defaultValues?.filterByYear as string[]).filter((elm) => elm !== "")
      : [];

    const common = {
      "hurdles-cost": defaultValues?.hurdleCost,
      "loop-flow": defaultValues?.loopFlows,
      "use-phase-shifter": defaultValues?.pst,
      "transmission-capacities": defaultValues?.transmissionCapa,
      "filter-synthesis": defaultFilterSynthesis.join(","),
      "filter-year-by-year": defaultFilterByYear.join(","),
    };

    let other = {
      "asset-type": "other",
      "link-style": "dot",
      "link-width": 2,
      colorr: 255,
      colorg: 128,
      colorb: 0,
    };
    switch (value) {
      case "ac":
        other = {
          "asset-type": "ac",
          "link-style": "plain",
          "link-width": 1,
          colorr: 112,
          colorg: 112,
          colorb: 112,
        };
        break;

      case "dc":
        other = {
          "asset-type": "dc",
          "link-style": "dash",
          "link-width": 2,
          colorr: 0,
          colorg: 255,
          colorb: 0,
        };
        break;

      case "gaz":
        other = {
          "asset-type": "gaz",
          "link-style": "plain",
          "link-width": 3,
          colorr: 0,
          colorg: 128,
          colorb: 255,
        };
        break;

      case "virt":
        other = {
          "asset-type": "virt",
          "link-style": "dotdash",
          "link-width": 2,
          colorr: 255,
          colorg: 0,
          colorb: 128,
        };
        break;

      default:
        break;
    }
    handleAutoSubmit(path.type, { ...common, ...other });
  };

  const renderSelect = (
    filterName: string,
    options: Array<{ label: string; value: string }>,
    onAutoSubmit?: AutoSubmitHandler,
  ) => (
    <SelectFE
      name={filterName}
      options={options}
      label={t(`study.modelization.links.${filterName}`)}
      control={control}
      rules={{
        onAutoSubmit:
          onAutoSubmit ||
          ((value) => {
            handleAutoSubmit(path[filterName], value);
          }),
      }}
    />
  );

  return (
    <Box
      sx={{
        width: "100%",
        height: "100%",
      }}
    >
      <Box
        sx={{
          display: "flex",
          flexDirection: "column",
        }}
      >
        <Fieldset legend={t("global.general")}>
          <SwitchFE
            name="hurdleCost"
            label={t("study.modelization.links.hurdleCost")}
            control={control}
            rules={{
              onAutoSubmit: (value) => handleAutoSubmit(path.hurdleCost, value),
            }}
          />
          <SwitchFE
            name="loopFlows"
            label={t("study.modelization.links.loopFlows")}
            control={control}
            rules={{
              onAutoSubmit: (value) => handleAutoSubmit(path.loopFlows, value),
            }}
          />
          <SwitchFE
            name="pst"
            label={t("study.modelization.links.pst")}
            control={control}
            rules={{
              onAutoSubmit: (value) => handleAutoSubmit(path.pst, value),
            }}
          />
          {renderSelect("transmissionCapa", optionTransCap)}
          {renderSelect("type", optionType, handleTypeAutoSubmit)}
        </Fieldset>
        <OutputFilters
          control={control}
          onAutoSubmit={(filterName, value) => handleAutoSubmit(path[filterName], value)}
        />
        <Box
          sx={{
            width: "100%",
            display: "flex",
            flexDirection: "column",
            height: "70vh",
          }}
        >
          {isTabMatrix ? (
            <LinkMatrixView study={study} area1={area1} area2={area2} />
          ) : (
            <Matrix
              url={`input/links/${area1.toLowerCase()}/${area2.toLowerCase()}`}
              customColumns={columnsNames}
            />
          )}
        </Box>
      </Box>
    </Box>
  );
}

export default LinkForm;
