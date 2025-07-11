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

import React from "react";
import { useTranslation } from "react-i18next";
import { Box, Tab, Tabs } from "@mui/material";
import ButtonBack from "../../../../../../common/ButtonBack";
import PropertiesView from "../../../../../../common/PropertiesView";
import ListElement from "../../../common/ListElement";
import { OutputItemType } from "../utils";
import type { PartialStudyOutput } from "../../hooks/useStudyOutput";

interface ResultItemSelectorProps {
  itemType: OutputItemType;
  onItemTypeChange: (_event: React.SyntheticEvent, newValue: OutputItemType) => void;
  output: PartialStudyOutput | undefined;
  filteredItems: Array<{ id: string; name: string; label?: string }>;
  selectedItemId: string;
  onSetSelectedItemId: (item: { id: string }) => void;
  onSearchChange: (value: string) => void;
  onNavigateBack: () => void;
}

function ResultItemSelector({
  itemType,
  onItemTypeChange,
  output,
  filteredItems,
  selectedItemId,
  onSetSelectedItemId,
  onSearchChange,
  onNavigateBack,
}: ResultItemSelectorProps) {
  const { t } = useTranslation();

  return (
    <Box>
      <PropertiesView
        topContent={
          <Box sx={{ width: 1, px: 1 }}>
            <ButtonBack onClick={onNavigateBack} />
          </Box>
        }
        mainContent={
          <>
            <Tabs
              value={itemType}
              onChange={onItemTypeChange}
              size="extra-small"
              variant="fullWidth"
            >
              <Tab label={t("study.areas")} value={OutputItemType.Areas} />
              <Tab label={t("study.links")} value={OutputItemType.Links} />
              {output?.synthesis && (
                <Tab label={t("study.synthesis")} value={OutputItemType.Synthesis} />
              )}
            </Tabs>
            <ListElement
              list={filteredItems}
              currentElement={selectedItemId}
              currentElementKeyToTest="id"
              setSelectedItem={onSetSelectedItemId}
            />
          </>
        }
        onSearchFilterChange={onSearchChange}
      />
    </Box>
  );
}

export default ResultItemSelector;
