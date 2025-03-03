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
import { TextField } from "@mui/material";
import { StudyOutputDownloadType, type Area, type Set } from "../../../../../../types/types";
import SelectMulti from "../../../../../common/SelectMulti";
import { Root } from "./style";
import MultipleLinkElement from "./MultipleLinkElement";
import SingleLinkElement from "./SingleLinkElement";

interface PropTypes {
  type: StudyOutputDownloadType;
  areas: Record<string, Area>;
  sets: Record<string, Set>;
  filterValue: string[];
  setFilterValue: (elm: string[]) => void;
  filterInValue: string;
  setFilterInValue: (elm: string) => void;
  filterOutValue: string;
  setFilterOutValue: (elm: string) => void;
}

function Filter(props: PropTypes) {
  const [t] = useTranslation();
  const {
    type,
    areas,
    sets,
    filterValue,
    filterInValue,
    filterOutValue,
    setFilterValue,
    setFilterInValue,
    setFilterOutValue,
  } = props;
  const [areasOrDistrictsList, setAreasOrDistrictsList] = useState<string[]>([]);

  useEffect(() => {
    const getAreasOrDistrictsList = (): string[] => {
      let res: string[] = [];
      switch (type) {
        case StudyOutputDownloadType.AREAS:
          res = Object.keys(areas);
          break;

        case StudyOutputDownloadType.DISTRICT:
          res = Object.keys(sets);
          break;

        default:
          break;
      }
      return res;
    };
    setAreasOrDistrictsList(getAreasOrDistrictsList());
  }, [areas, sets, type]);

  return type !== StudyOutputDownloadType.LINKS ? (
    <Root>
      <SelectMulti
        name={t("global.filterAction")}
        list={areasOrDistrictsList.map((elm) => ({ id: elm, name: elm }))}
        data={filterValue}
        setValue={(elm: string[] | string) => setFilterValue(elm as string[])}
        sx={{ m: 0, mb: 2, width: "95%" }}
        required
      />
      <TextField
        label={t("study.filterIn")}
        value={filterInValue}
        onChange={(event) => setFilterInValue(event.target.value)}
        sx={{ m: 0, mb: 2, width: "95%" }}
      />
      <TextField
        label={t("study.filterOut")}
        value={filterOutValue}
        onChange={(event) => setFilterOutValue(event.target.value)}
        sx={{ m: 0, mb: 2, width: "95%" }}
      />
    </Root>
  ) : (
    <Root>
      <MultipleLinkElement
        label={t("global.filterAction")}
        areas={Object.keys(areas)}
        values={filterValue}
        onChange={setFilterValue}
      />
      <SingleLinkElement label={t("study.filterIn")} onChange={setFilterInValue} />
      <SingleLinkElement label={t("study.filterOut")} onChange={setFilterOutValue} />
    </Root>
  );
}

export default Filter;
