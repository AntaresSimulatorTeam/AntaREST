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

// @flow
import { useState } from "react";
import type { DraggableProvided } from "react-beautiful-dnd";
import ReactJson, { type InteractionProps } from "react-json-view";
import ExpandMore from "@mui/icons-material/ExpandMore";
import SaveOutlinedIcon from "@mui/icons-material/SaveOutlined";
import CloudDownloadOutlinedIcon from "@mui/icons-material/CloudDownloadOutlined";
import InfoIcon from "@mui/icons-material/Info";
import {
  AccordionDetails,
  AccordionSummary,
  Box,
  CircularProgress,
  styled,
  Typography,
} from "@mui/material";
import type { CommandItem } from "../../commandTypes";
import CommandImportButton from "../CommandImportButton";
import type { CommandResultDTO } from "../../../../../../../types/types";
import LogModal from "../../../../../../common/LogModal";
import {
  detailsStyle,
  DraggableAccorderon,
  Header,
  headerIconStyle,
  Info,
  ItemContainer,
  JsonContainer,
  StyledDeleteIcon,
} from "./style";
import CommandMatrixViewer from "./CommandMatrixViewer";
import CommandDetails from "./CommandDetails";

export const Item = styled(Box)(({ theme }) => ({
  boxSizing: "border-box",
  display: "flex",
  flexFlow: "row nowrap",
  justifyContent: "space-between",
  alignItems: "flex-start",
  width: "100%",
}));

interface StyleType {
  provided: DraggableProvided;
  style: React.CSSProperties;
  isDragging: boolean;
}
function getStyle({ provided, style, isDragging }: StyleType) {
  // If you don't want any spacing between your items
  // then you could just return this.
  // I do a little bit of magic to have some nice visual space
  // between the row items
  const combined = {
    ...style,
    ...provided.draggableProps.style,
  };

  const marginBottom = 8;
  const withSpacing = {
    ...combined,
    height: isDragging ? combined.height : (combined.height as number) - marginBottom,
    marginBottom,
  };
  return withSpacing;
}

interface PropsType {
  provided: DraggableProvided;
  item: CommandItem;
  style: React.CSSProperties;
  isDragging: boolean;
  index: number;
  generationStatus: boolean;
  generationIndex: number;
  onDelete: (index: number) => void;
  onArgsUpdate: (index: number, json: object) => void;
  onSave: (index: number) => void;
  onCommandImport: (index: number, json: object) => void;
  onCommandExport: (index: number) => void;
  onExpanded: (index: number, value: boolean) => void;
  expandedIndex: number;
}

function CommandListItem({
  provided,
  item,
  style,
  isDragging,
  index,
  generationStatus,
  generationIndex,
  expandedIndex,
  onDelete,
  onArgsUpdate,
  onSave,
  onCommandImport,
  onCommandExport,
  onExpanded,
}: PropsType) {
  const [jsonData, setJsonData] = useState<object>(item.args);
  const [logModalOpen, setLogModalOpen] = useState<boolean>(false);

  const updateJson = (e: InteractionProps) => {
    setJsonData(e.updated_src);
    onArgsUpdate(index, e.updated_src);
  };

  const onImport = async (json: object) => {
    // setJsonData((json as any)['args']);
    const oldJson = { ...jsonData };
    try {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      setJsonData(json as any);
      await onCommandImport(index, json);
    } catch {
      setJsonData(oldJson);
    }
  };

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
    <ItemContainer
      {...provided.draggableProps}
      {...provided.dragHandleProps}
      ref={provided.innerRef}
      style={getStyle({ provided, style, isDragging })}
      onTopVisible={expandedIndex === index}
    >
      <Item>
        <DraggableAccorderon isDragging={isDragging} expanded={expandedIndex === index}>
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
              <Header>
                {item.updated && (
                  <SaveOutlinedIcon sx={{ ...headerIconStyle }} onClick={() => onSave(index)} />
                )}
                {!generationStatus && <CommandImportButton onImport={onImport} />}
                {!generationStatus && (
                  <CloudDownloadOutlinedIcon
                    sx={{ ...headerIconStyle }}
                    onClick={() => onCommandExport(index)}
                  />
                )}
              </Header>
              <JsonContainer>
                <ReactJson
                  src={jsonData}
                  onEdit={!generationStatus ? updateJson : undefined}
                  onDelete={!generationStatus ? updateJson : undefined}
                  onAdd={!generationStatus ? updateJson : undefined}
                  theme="monokai"
                />
              </JsonContainer>
              <CommandMatrixViewer command={item} />
            </Box>
          </AccordionDetails>
        </DraggableAccorderon>
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
