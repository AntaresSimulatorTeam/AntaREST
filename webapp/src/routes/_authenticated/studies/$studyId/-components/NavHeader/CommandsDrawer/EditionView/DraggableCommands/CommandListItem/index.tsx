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

import JSONEditor from "@/components/JSONEditor";
import LogModal from "@/components/LogModal";
import ExpandMore from "@mui/icons-material/ExpandMore";
import InfoIcon from "@mui/icons-material/Info";
import {
  AccordionDetails,
  AccordionSummary,
  Box,
  CircularProgress,
  styled,
  Typography,
} from "@mui/material";
import { useState } from "react";
import type { CommandResultDTO } from "../../../../../../../../../../types/types";
import type { CommandItem } from "../../commandTypes";
import CommandDetails from "./CommandDetails";
import CommandMatrixViewer from "./CommandMatrixViewer";
import {
  detailsStyle,
  headerIconStyle,
  Info,
  ItemContainer,
  JsonContainer,
  StyledAccordion,
  StyledDeleteIcon,
} from "./style";

export const Item = styled(Box)(({ theme }) => ({
  boxSizing: "border-box",
  display: "flex",
  flexFlow: "row nowrap",
  justifyContent: "space-between",
  alignItems: "flex-start",
  width: "100%",
}));

interface PropsType {
  item: CommandItem;
  style: React.CSSProperties;
  index: number;
  generationStatus: boolean;
  generationIndex: number;
  onDelete: (index: number) => void;
  onExpanded: (index: number, value: boolean) => void;
  expandedIndex: number;
}

function CommandListItem({
  item,
  style,
  index,
  generationStatus,
  generationIndex,
  expandedIndex,
  onDelete,
  onExpanded,
}: PropsType) {
  const [logModalOpen, setLogModalOpen] = useState<boolean>(false);

  const itemElements = () => {
    if (generationStatus && generationIndex === index) {
      return (
        <CircularProgress
          color="primary"
          sx={{ width: "24px", height: "24px", margin: "0px 16px" }}
        />
      );
    }
    return (
      <>
        {!generationStatus && <StyledDeleteIcon onClick={() => onDelete(index)} />}
        {item.results !== undefined && (
          <InfoIcon
            sx={{
              ...headerIconStyle,
              color: (item.results as CommandResultDTO).success ? "success.main" : "error.main",
              "&:header": {
                color: (item.results as CommandResultDTO).success ? "success.dark" : "error.dark",
              },
            }}
            onClick={() => setLogModalOpen(true)}
          />
        )}
      </>
    );
  };

  return (
    <ItemContainer style={style} onTopVisible={expandedIndex === index}>
      <Item>
        <StyledAccordion expanded={expandedIndex === index}>
          <AccordionSummary
            expandIcon={<ExpandMore />}
            aria-controls="panel1a-content"
            id="panel1a-header"
            onClick={() => onExpanded(index, !(expandedIndex === index))}
          >
            <Info>
              <Typography sx={{ px: 0.5, mb: 0.5 }}>{item.action}</Typography>
              <CommandDetails item={item} />
            </Info>
          </AccordionSummary>
          <AccordionDetails sx={{ ...detailsStyle }}>
            <Box sx={{ ...detailsStyle }}>
              <JsonContainer>
                <JSONEditor
                  json={item.args}
                  mode="view"
                  mainMenuBar={false}
                  navigationBar={false}
                  sx={{ width: 1 }}
                />
              </JsonContainer>
              <CommandMatrixViewer command={item} />
            </Box>
          </AccordionDetails>
        </StyledAccordion>
        <Box
          sx={{
            height: "50px",
            width: "80px",
            display: "flex",
            justifyContent: "flex-start",
            alignItems: "center",
            boxSizing: "border-box",
          }}
        >
          {itemElements()}
        </Box>
      </Item>
      {item.results !== undefined && (
        <LogModal
          isOpen={logModalOpen}
          content={item.results.message}
          close={() => setLogModalOpen(false)}
        />
      )}
    </ItemContainer>
  );
}

export default CommandListItem;
