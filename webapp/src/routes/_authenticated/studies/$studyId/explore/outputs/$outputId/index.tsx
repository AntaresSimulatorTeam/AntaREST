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
import ListView, { type ListViewItem } from "@/components/page/list/ListView";
import useStudySynthesis from "@/redux/hooks/useStudySynthesis";
import { sortByName } from "@/services/utils";
import AutoAwesomeMotionIcon from "@mui/icons-material/AutoAwesomeMotion";
import AccountTreeOutlinedIcon from "@mui/icons-material/AccountTreeOutlined";
import { Box, Chip, Stack, Tab, Tabs, Typography } from "@mui/material";
import { createFileRoute } from "@tanstack/react-router";
import { useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import useAppSelector from "../../../../../../../redux/hooks/useAppSelector";
import { getAreas, getDistricts, getLinks } from "../../../../../../../redux/selectors";
import OutputMatrixViewer from "./-components/OutputMatrixViewer";
import OutputWorkspaceDraft from "./-components/OutputWorkspaceDraft";
import CategoryNavigation, {
  type ResultCategory,
} from "./-components/OutputWorkspaceDraft/CategoryNavigation";
import SynthesisViewer from "./-components/SynthesisViewer";
import useOutput from "./-hooks/useOutput";
import { isDistrict, SYNTHESIS_ITEMS, type GridType, type Item, type ListType } from "./-utils";

export const Route = createFileRoute("/_authenticated/studies/$studyId/explore/outputs/$outputId/")(
  {
    component: Output,
  },
);

function Output() {
  const { t } = useTranslation();
  const { studyId } = Route.useParams();
  const [listType, setListType] = useState<ListType>("areas");
  const [selectedCategoryId, setSelectedCategoryId] = useState("areas");
  const output = useOutput();
  const isBaseline = new URLSearchParams(window.location.search).get("design") === "baseline";

  const categories: ResultCategory[] = [
    { id: "areas", label: t("study.areas") },
    { id: "links", label: t("study.links") },
    ...(output.synthesis ? [{ id: "synthesis", label: t("study.synthesis") }] : []),
    {
      id: "dispatchable",
      label: t("outputDesign.category.dispatchable"),
      example: true,
    },
    {
      id: "renewable",
      label: t("outputDesign.category.renewable"),
      example: true,
    },
    { id: "demand", label: t("outputDesign.category.demand"), example: true },
    {
      id: "shortTermStorage",
      label: t("outputDesign.category.shortTermStorage"),
      example: true,
    },
    {
      id: "longTermStorage",
      label: t("outputDesign.category.longTermStorage"),
      example: true,
    },
    {
      id: "investments",
      label: t("outputDesign.category.investments"),
      example: true,
    },
  ];
  const selectedCategory = categories.find(({ id }) => id === selectedCategoryId) ?? categories[0];

  useStudySynthesis({ studyId });
  const areas = useAppSelector((state) => getAreas(state, studyId));
  const districts = useAppSelector((state) => getDistricts(state, studyId));
  const links = useAppSelector((state) => getLinks(state, studyId));

  const list = useMemo<Array<ListViewItem<Item | GridType>>>(() => {
    if (listType === "areas") {
      const adaptedDistricts = districts.map((district) => ({
        ...district,
        // In the `output` folder of the studies, district and area folders share the same
        // hierarchy level. Area folders are named using their IDs, whereas district folders
        // are named using the `@ ` prefix followed by their IDs.
        id: `@ ${district.id}`,
      }));

      // Areas are already sorted in redux state
      return [...areas, ...sortByName(adaptedDistricts)].map((item) => ({
        id: item.id,
        label: item.name,
        icon: isDistrict(item) ? <AutoAwesomeMotionIcon color="info" /> : undefined,
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

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleListTypeChange = (_event: React.SyntheticEvent, newType: ListType) => {
    setListType(newType);
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  const baselineView = (
    <ListView
      splitId="results"
      // Minimum left panel size to prevent the tabs scrollbar (supports EN and FR label lengths)
      splitMinSize={[293, 150]}
      list={list}
      disableSearch={listType === "synthesis"}
      multipleSearch
      actions={
        <Stack sx={{ overflow: "auto" }}>
          <BackButton linkOptions={{ to: ".." }} />
          <Tabs value={listType} onChange={handleListTypeChange} size="extra-small">
            <Tab label={t("study.areas")} value="areas" />
            <Tab label={t("study.links")} value="links" />
            {output.synthesis && <Tab label={t("study.synthesis")} value="synthesis" />}
          </Tabs>
        </Stack>
      }
      renderItemView={({ data }) => {
        if (!data) {
          return null;
        }

        if (typeof data === "string") {
          return <SynthesisViewer gridType={data} />;
        }

        return <OutputMatrixViewer item={data} />;
      }}
    />
  );

  if (isBaseline) {
    return baselineView;
  }

  const exampleView = (
    <Stack
      direction="column"
      alignItems="center"
      justifyContent="center"
      spacing={1.5}
      sx={{ height: 1, p: 4, textAlign: "center" }}
    >
      <AccountTreeOutlinedIcon sx={{ fontSize: 42, color: "text.disabled" }} />
      <Typography variant="h6">{selectedCategory.label}</Typography>
      <Chip label={t("outputDesign.exampleTaxonomy")} size="small" />
      <Typography variant="body2" color="text.secondary" sx={{ maxWidth: 410 }}>
        {t("outputDesign.exampleExplanation")}
      </Typography>
    </Stack>
  );

  return (
    <OutputWorkspaceDraft key={output.id} outputName={output.name}>
      {({ variant, filesActive, fileCount, onOpenFiles, onShowResults, filesPanel }) => {
        const explorerFilesActive = variant === "explorer" && filesActive;
        const renderContent = (content: React.ReactNode) => (
          <Box sx={{ height: 1, minHeight: 0, overflow: "hidden" }}>
            <Box
              sx={{
                height: 1,
                display: explorerFilesActive ? "none" : "block",
              }}
            >
              {content}
            </Box>
            {explorerFilesActive && filesPanel}
          </Box>
        );

        return (
          <Box
            sx={{
              height: 1,
              "& .SplitView > :first-child": { minWidth: 270 },
              "& .SplitView > :last-child": { flex: 1, minWidth: 0 },
              "& .SplitView > .MuiStack-root > .MuiList-root": {
                display: explorerFilesActive ? "none" : undefined,
              },
            }}
          >
            <ListView
              splitId="results-design"
              splitMinSize={[270, 150]}
              list={selectedCategory.example ? [] : list}
              disableSearch={
                explorerFilesActive || selectedCategory.example || listType === "synthesis"
              }
              multipleSearch
              emptyListView={renderContent(exampleView)}
              actions={
                <CategoryNavigation
                  categories={categories}
                  value={selectedCategory}
                  variant={variant}
                  filesActive={explorerFilesActive}
                  fileCount={fileCount}
                  onOpenFiles={onOpenFiles}
                  onChange={(category) => {
                    setSelectedCategoryId(category.id);
                    if (
                      category.id === "areas" ||
                      category.id === "links" ||
                      category.id === "synthesis"
                    ) {
                      setListType(category.id);
                    }
                    onShowResults();
                  }}
                />
              }
              renderItemView={({ data }) =>
                renderContent(
                  !data ? null : typeof data === "string" ? (
                    <SynthesisViewer gridType={data} />
                  ) : (
                    <OutputMatrixViewer item={data} />
                  ),
                )
              }
            />
          </Box>
        );
      }}
    </OutputWorkspaceDraft>
  );
}
