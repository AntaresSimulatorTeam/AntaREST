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

import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import range from "lodash/range";
import { Box, Checkbox, FormControlLabel, styled } from "@mui/material";
import {
  StudyOutputDownloadLevelDTO,
  StudyOutputDownloadType,
  type Area,
  type Set as District,
  type FileStudyTreeConfigDTO,
  type StudyOutputDownloadDTO,
} from "../../../../../types/types";
import Filter from "./Filter";
import TagSelect from "./TagSelect";
import SelectSingle from "../../../../common/SelectSingle";
import SelectMulti from "../../../../common/SelectMulti";

const Root = styled(Box)(({ theme }) => ({
  flex: 1,
  width: "100%",
  display: "flex",
  flexFlow: "column nowrap",
  justifyContent: "flex-start",
  alignItems: "flex-start",
  padding: theme.spacing(1, 0),
}));

interface PropTypes {
  output: string;
  synthesis: FileStudyTreeConfigDTO | undefined;
  filter: StudyOutputDownloadDTO;
  setFilter: (filter: StudyOutputDownloadDTO) => void;
}

function ExportFilterModal(props: PropTypes) {
  const [t] = useTranslation();
  const { output, synthesis, filter, setFilter } = props;
  const [year, setYear] = useState<number[]>([]);
  const [byYear, setByYear] = useState<{ isByYear: boolean; nbYear: number }>({
    isByYear: false,
    nbYear: -1,
  });
  const [areaList, setAreaList] = useState<Record<string, Area>>({});
  const [districtList, setDistrictList] = useState<Record<string, District>>({});

  const typeList: string[] = [
    StudyOutputDownloadType.AREAS,
    StudyOutputDownloadType.LINKS,
    StudyOutputDownloadType.DISTRICT,
  ];
  const levelList: string[] = [
    StudyOutputDownloadLevelDTO.HOURLY,
    StudyOutputDownloadLevelDTO.DAILY,
    StudyOutputDownloadLevelDTO.WEEKLY,
    StudyOutputDownloadLevelDTO.MONTHLY,
    StudyOutputDownloadLevelDTO.ANNUAL,
  ];

  const onTypeChange = (value: string[] | string): void => {
    setFilter({
      ...filter,
      filter: [],
      filterIn: "",
      filterOut: "",
      type: value as StudyOutputDownloadType,
    });
  };

  const onLevelChange = (value: string[] | string): void => {
    setFilter({ ...filter, level: value as StudyOutputDownloadLevelDTO });
  };

  useEffect(() => {
    if (synthesis) {
      if (output in synthesis.outputs) {
        const outputs = synthesis.outputs[output];
        setByYear({ isByYear: outputs?.by_year, nbYear: outputs?.nbyears });
        setAreaList(synthesis.areas);
        setDistrictList(synthesis.sets);
      }
    }
  }, [synthesis, output]);

  return (
    <Root>
      <SelectSingle
        name={t("study.type")}
        list={typeList.map((elm) => ({
          id: elm,
          name: t(`study.${elm.toLowerCase()}`),
        }))}
        data={filter.type}
        setValue={(data: string) => onTypeChange(data)}
        sx={{ width: "300px", mb: 2 }}
        required
      />
      {byYear.isByYear && byYear.nbYear > 0 && (
        <SelectMulti
          name={t("study.years")}
          list={range(byYear.nbYear).map((elm) => ({
            id: elm.toString(),
            name: elm.toString(),
          }))}
          data={year.map((elm) => elm.toString())}
          setValue={(value: string[] | string) =>
            setYear((value as string[]).map((elm) => parseInt(elm, 10)))
          }
          sx={{ width: "100%", mb: 2 }}
          required
        />
      )}
      <SelectSingle
        name={t("study.level")}
        list={levelList.map((elm) => ({
          id: elm,
          name: t(`study.${elm.toLowerCase()}`),
        }))}
        data={filter.level}
        setValue={(data: string) => onLevelChange(data)}
        sx={{ width: "300px", mb: 2 }}
      />
      <TagSelect
        label={t("study.columns")}
        values={filter.columns !== undefined ? filter.columns : []}
        onChange={(value: string[]) => setFilter({ ...filter, columns: value })}
      />
      <Filter
        type={filter.type}
        areas={areaList}
        sets={districtList}
        filterValue={filter.filter ? filter.filter : []}
        setFilterValue={(elm: string[]) => setFilter({ ...filter, filter: elm })}
        filterInValue={filter.filterIn ? filter.filterIn : ""}
        setFilterInValue={(elm: string) => setFilter({ ...filter, filterIn: elm })}
        filterOutValue={filter.filterOut ? filter.filterOut : ""}
        setFilterOutValue={(elm: string) => setFilter({ ...filter, filterOut: elm })}
      />
      <FormControlLabel
        control={
          <Checkbox
            checked={filter.synthesis}
            onChange={(e, checked) => setFilter({ ...filter, synthesis: checked })}
            name={t("study.synthesis")}
          />
        }
        sx={{ my: 1 }}
        label={t("study.synthesis")}
      />
      <FormControlLabel
        control={
          <Checkbox
            checked={filter.includeClusters}
            onChange={(e, checked) => setFilter({ ...filter, includeClusters: checked })}
            name={t("study.includeClusters")}
          />
        }
        label={t("study.includeClusters")}
      />
    </Root>
  );
}

export default ExportFilterModal;
