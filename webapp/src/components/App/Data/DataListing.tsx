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

import { memo } from "react";
import { Typography, Box, styled } from "@mui/material";
import AutoSizer from "react-virtualized-auto-sizer";
import { FixedSizeList, areEqual, type ListChildComponentProps } from "react-window";
import ArrowRightIcon from "@mui/icons-material/ArrowRight";
import type { MatrixDataSetDTO } from "../../../types/types";

const ROW_ITEM_SIZE = 45;
const BUTTONS_SIZE = 40;

const StyledList = styled(FixedSizeList)(({ theme }) => ({
  "&> div > div": {
    cursor: "pointer",
    "&:hover": {
      textDecoration: "underline",
      color: theme.palette.text.primary,
      "&>svg": {
        color: `${theme.palette.text.primary} !important`,
      },
    },
  },
}));

interface PropsType {
  datasets: MatrixDataSetDTO[] | undefined;
  selectedItem: string;
  setSelectedItem: (item: string) => void;
}

const Row = memo((props: ListChildComponentProps) => {
  const { data, index, style } = props;
  const { datasets, setSelectedItem, selectedItem } = data;
  const dataset = datasets[index];

  return (
    <Box
      sx={
        selectedItem && selectedItem === dataset.id
          ? {
              display: "flex",
              justifyContent: "space-evenly",
              alignItems: "center",
              ...style,
              textDecoration: "underline",
              color: "white",
            }
          : {
              display: "flex",
              justifyContent: "space-evenly",
              alignItems: "center",
              ...style,
            }
      }
      onClick={() => {
        setSelectedItem(dataset.id);
      }}
    >
      <Typography
        sx={{
          display: "block",
          width: "200px",
          textOverflow: "ellipsis",
          overflow: "hidden",
        }}
      >
        {dataset.name}
      </Typography>
      <ArrowRightIcon />
    </Box>
  );
}, areEqual);

Row.displayName = "Row";

function DataListing(props: PropsType) {
  const { datasets = [], selectedItem, setSelectedItem } = props;

  return (
    <Box
      sx={{
        width: "100%",
        minHeight: "100px",
        color: "text.secondary",
        display: "flex",
        flexGrow: 1,
        flexShrink: 1,
        marginBottom: "10px",
      }}
    >
      {datasets && datasets.length > 0 && (
        <AutoSizer>
          {({ height, width }) => {
            const idealHeight = ROW_ITEM_SIZE * datasets.length;
            return (
              <StyledList
                height={idealHeight > height ? height + ROW_ITEM_SIZE - BUTTONS_SIZE : idealHeight}
                width={width}
                itemCount={datasets.length}
                itemSize={ROW_ITEM_SIZE}
                itemData={{
                  datasets,
                  setSelectedItem,
                  selectedItem,
                }}
              >
                {Row}
              </StyledList>
            );
          }}
        </AutoSizer>
      )}
    </Box>
  );
}

export default DataListing;
