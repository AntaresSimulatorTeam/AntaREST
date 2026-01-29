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
import PropertiesView from "@/components/PropertiesView";
import { Box, Tab, Tabs } from "@mui/material";
import { useTranslation } from "react-i18next";
import type { PartialStudyOutput } from "../-hooks/useStudyOutput";
import type { OutputItemType } from "../-utils";
import ListElement from "../../../../../../../../components/ListElement";

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

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <Box>
      <PropertiesView
        topContent={
          <Box sx={{ width: 1, px: 1 }}>
            <BackButton linkOptions={{ to: ".." }} />
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
              <Tab label={t("study.areas")} value="areas" />
              <Tab label={t("study.links")} value="links" />
              {output?.synthesis && <Tab label={t("study.synthesis")} value="synthesis" />}
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
