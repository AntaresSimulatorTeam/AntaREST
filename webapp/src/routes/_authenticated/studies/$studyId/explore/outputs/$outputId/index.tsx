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

import BackButton from "@/components/buttons/BackButton";
import ListView, { type ContentListItem } from "@/components/page/ListView";
import usePromiseWithSnackbarError from "@/hooks/usePromiseWithSnackbarError";
import { getStudyDistricts } from "@/services/api/study";
import AutoAwesomeMotionIcon from "@mui/icons-material/AutoAwesomeMotion";
import { Stack, Tab, Tabs } from "@mui/material";
import { createFileRoute } from "@tanstack/react-router";
import { useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import useAppSelector from "../../../../../../../redux/hooks/useAppSelector";
import { getAreas, getLinks } from "../../../../../../../redux/selectors";
import OutputMatrixViewer from "./-components/OutputMatrixViewer";
import SynthesisViewer from "./-components/SynthesisViewer";
import useStudyOutput from "./-hooks/useStudyOutput";
import { SYNTHESIS_ITEMS, type Item, type ListType } from "./-utils";

export const Route = createFileRoute("/_authenticated/studies/$studyId/explore/outputs/$outputId/")(
  {
    component: Output,
  },
);

function Output() {
  const { t } = useTranslation();
  const { studyId, outputId } = Route.useParams();
  const [listType, setListType] = useState<ListType>("areas");

  const areas = useAppSelector((state) => getAreas(state, studyId));
  const links = useAppSelector((state) => getLinks(state, studyId));

  const { data: districts = [] } = usePromiseWithSnackbarError(() => getStudyDistricts(studyId), {
    deps: [studyId],
    errorMessage: t("study.outputs.loadDistrictsError"), // TODO text
  });

  const { data: output } = useStudyOutput({ studyId, outputId });

  const list = useMemo<Array<ContentListItem<Item>>>(() => {
    if (listType === "areas") {
      return [...areas, ...districts].map((item) => ({
        id: item.id,
        label: item.name,
        icon: "areas" in item ? <AutoAwesomeMotionIcon color="info" /> : undefined,
        data: item,
      }));
    }
    if (listType === "links") {
      return links.map((link) => ({
        id: link.id,
        label: link.label,
        data: link,
      }));
    }
    if (listType === "synthesis") {
      return SYNTHESIS_ITEMS;
    }
    return [];
  }, [listType, areas, districts, links]);

  ///////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleListTypeChange = (_event: React.SyntheticEvent, newType: ListType) => {
    setListType(newType);
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <ListView
      splitId="results"
      splitMinSize={[280, 150]}
      list={list}
      actions={
        <Stack>
          <BackButton linkOptions={{ to: ".." }} />
          <Tabs value={listType} onChange={handleListTypeChange} size="extra-small">
            <Tab label={t("study.areas")} value="areas" />
            <Tab label={t("study.links")} value="links" />
            {output?.synthesis && <Tab label={t("study.synthesis")} value="synthesis" />}
          </Tabs>
        </Stack>
      }
      renderItemContent={({ id, data }) => {
        return !data ? (
          <SynthesisViewer gridId={id} />
        ) : (
          <OutputMatrixViewer output={output} selectedItem={data} />
        );
      }}
    />
  );
}
