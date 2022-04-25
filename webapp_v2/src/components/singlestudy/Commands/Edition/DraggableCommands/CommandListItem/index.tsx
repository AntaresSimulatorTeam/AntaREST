// @flow
import { CSSProperties, useState } from "react";
import { useTranslation } from "react-i18next";
import { DraggableProvided } from "react-beautiful-dnd";
import ReactJson, { InteractionProps } from "react-json-view";
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
import { CommandItem } from "../../CommandTypes";
import CommandImportButton from "../CommandImportButton";
import { CommandResultDTO } from "../../../../../../common/types";
import LogModal from "../../../../../common/LogModal";
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
import { scrollbarStyle } from "../../../../../../theme";

export const Item = styled(Box)(({ theme }) => ({
  boxSizing: "border-box",
  display: "flex",
  flexFlow: "row nowrap",
  justifyContent: "space-between",
  alignItems: "flex-start",
  width: "100%",
  height: "auto",
  userSelect: "none",
  maxWidth: "800px",
}));

interface StyleType {
  provided: DraggableProvided;
  style: CSSProperties;
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
    height: isDragging
      ? combined.height
      : (combined.height as number) - marginBottom,
    marginBottom,
  };
  return withSpacing;
}

interface PropsType {
  provided: DraggableProvided;
  item: CommandItem;
  style: CSSProperties;
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
  const [t] = useTranslation();
  const [jsonData, setJsonData] = useState<object>(item.args);
  const [logModalOpen, setLogModalOpen] = useState<boolean>(false);

  const updateJson = (e: InteractionProps) => {
    setJsonData(e.updated_src);
    onArgsUpdate(index, e.updated_src);
  };

  const onImport = async (json: object) => {
    // eslint-disable-next-line dot-notation
    // setJsonData((json as any)['args']);
    const oldJson = { ...jsonData };
    try {
      setJsonData(json as any);
      await onCommandImport(index, json);
    } catch (e) {
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
        {!generationStatus && (
          <StyledDeleteIcon onClick={() => onDelete(index)} />
        )}
        {item.results !== undefined && (
          <InfoIcon
            sx={{
              ...headerIconStyle,
              color: (item.results as CommandResultDTO).success
                ? "success.main"
                : "error.main",
              "&:header": {
                color: (item.results as CommandResultDTO).success
                  ? "success.dark"
                  : "error.dark",
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
      // eslint-disable-next-line react/jsx-props-no-spreading
      {...provided.draggableProps}
      // eslint-disable-next-line react/jsx-props-no-spreading
      {...provided.dragHandleProps}
      ref={provided.innerRef}
      style={getStyle({ provided, style, isDragging })}
      onTopVisible={expandedIndex === index}
    >
      <Item>
        <DraggableAccorderon
          isDragging={isDragging}
          expanded={expandedIndex === index}
        >
          <AccordionSummary
            expandIcon={<ExpandMore />}
            aria-controls="panel1a-content"
            id="panel1a-header"
            onClick={() => onExpanded(index, !(expandedIndex === index))}
          >
            <Info>
              <Typography color="primary" style={{ fontSize: "0.9em" }}>
                {item.action}
              </Typography>
            </Info>
          </AccordionSummary>
          <AccordionDetails sx={{ ...detailsStyle }}>
            <Box sx={{ ...detailsStyle }}>
              <Header>
                {item.updated && (
                  <SaveOutlinedIcon
                    sx={{ ...headerIconStyle }}
                    onClick={() => onSave(index)}
                  />
                )}
                {!generationStatus && (
                  <CommandImportButton onImport={onImport} />
                )}
                {!generationStatus && (
                  <CloudDownloadOutlinedIcon
                    sx={{ ...headerIconStyle }}
                    onClick={() => onCommandExport(index)}
                  />
                )}
              </Header>
              <JsonContainer sx={{ ...scrollbarStyle }}>
                <ReactJson
                  src={jsonData}
                  onEdit={!generationStatus ? updateJson : undefined}
                  onDelete={!generationStatus ? updateJson : undefined}
                  onAdd={!generationStatus ? updateJson : undefined}
                  theme="monokai"
                />
              </JsonContainer>
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
          title={t("singlestudy:taskLog")}
          content={item.results.message}
          close={() => setLogModalOpen(false)}
          style={{ width: "400px", height: "200px" }}
        />
      )}
    </ItemContainer>
  );
}

export default CommandListItem;
