import { useEffect, useState } from "react";
import { ColorResult, HuePicker, MaterialPicker } from "react-color";
import {
  Box,
  Typography,
  TextField,
  Button,
  Divider,
  styled,
} from "@mui/material";
import { useTranslation } from "react-i18next";
import DeleteIcon from "@mui/icons-material/Delete";
import {
  NodeProperties,
  LinkProperties,
  UpdateAreaUi,
} from "../../../../../../common/types";
import LinksView from "./LinksView";
import ConfirmationDialog from "../../../../../common/dialogs/ConfirmationDialog";

export const StyledDeleteIcon = styled(DeleteIcon)(({ theme }) => ({
  cursor: "pointer",
  color: theme.palette.error.light,
  "&:hover": {
    color: theme.palette.error.main,
  },
}));

const StyledHuePicker = styled(HuePicker)(({ theme }) => ({
  width: "90% !important",
  margin: theme.spacing(1),
}));

const StyledMaterialPicker = styled(Box)(({ theme }) => ({
  "& > div > div:first-of-type": {
    backgroundColor: "rgba(0, 0, 0, 0.12) !important",
    boxShadow: "none !important",
  },
  "& > div > div:last-of-type > div": {
    width: "unset !important",
    height: "120px !important",
    maxWidth: "275px !important",
    fontFamily: '"Inter", sans-serif !important',
    boxShadow: "none",
    "& > div > input, > div > div > div > input": {
      backgroundColor: "rgba(0,0,0,0)",
      color: `${theme.palette.text.secondary} !important`,
    },
  },
}));

const StyledLinkTypo = styled(Typography)(({ theme }) => ({
  cursor: "pointer",
  color: theme.palette.text.secondary,
  padding: theme.spacing(1),
  "&:hover": {
    textDecoration: "underline",
    color: "white",
  },
}));

interface PropType {
  node?: NodeProperties;
  nodes?: Array<NodeProperties>;
  links?: Array<LinkProperties>;
  link?: LinkProperties;
  onDelete: (id: string, target?: string) => void;
  updateUI: (id: string, value: UpdateAreaUi) => void;
  setSelectedItem: (item: NodeProperties | LinkProperties | undefined) => void;
}

function PanelView(props: PropType) {
  const [t] = useTranslation();
  const { node, nodes, links, link, onDelete, updateUI, setSelectedItem } =
    props;
  const [openConfirmationModal, setOpenConfirmationModal] =
    useState<boolean>(false);
  const [currentColor, setCurrentColor] = useState<string>(node?.color || "");

  const handleChangeColor = (color: ColorResult) => {
    if (node) {
      setCurrentColor(`rgb(${color.rgb.r}, ${color.rgb.g}, ${color.rgb.b})`);
      updateUI(node.id, {
        x: node.x,
        y: node.y,
        color_rgb:
          color.rgb !== null
            ? [color.rgb.r, color.rgb.g, color.rgb.b]
            : node.color.slice(4, -1).split(",").map(Number),
      });
    }
  };

  const handleClick = (name: string) => {
    if (nodes) {
      setSelectedItem(nodes.find((o) => o.id === name));
    }
  };

  useEffect(() => {
    if (node?.color) {
      setCurrentColor(node.color);
    }
  }, [node]);

  return (
    <>
      <Box
        width="100%"
        display="flex"
        flexDirection="column"
        alignItems="center"
        flexGrow={1}
        sx={{ mb: 1 }}
      >
        {node && (
          <Box
            width="100%"
            display="flex"
            flexDirection="column"
            alignItems="center"
          >
            <TextField
              sx={{ mt: 1 }}
              label={t("study.modelization.map.areaName")}
              variant="filled"
              value={node.name}
              disabled
            />
            <TextField
              sx={{ mt: 1 }}
              label={t("study.modelization.posX")}
              variant="filled"
              value={node.x}
              disabled
            />
            <TextField
              sx={{ mt: 1 }}
              label={t("study.modelization.posY")}
              variant="filled"
              value={node.y}
              disabled
            />
            <StyledHuePicker
              color={currentColor}
              onChangeComplete={(color) => handleChangeColor(color)}
            />
            <StyledMaterialPicker>
              <MaterialPicker
                color={currentColor}
                onChangeComplete={(color) => handleChangeColor(color)}
              />
            </StyledMaterialPicker>
          </Box>
        )}
        {links && node && (
          <LinksView
            links={links}
            node={node}
            setSelectedItem={setSelectedItem}
          />
        )}
        {link && (
          <Box
            width="100%"
            display="flex"
            flexDirection="column"
            alignItems="center"
          >
            <Typography
              sx={{
                width: "90%",
                display: "flex",
                flexFlow: "row nowrap",
                justifyContent: "flex-start",
                alignItems: "center",
                boxSizing: "border-box",
                textDecoration: "underline",
                my: 1,
                color: "text.secondary",
              }}
            >
              {t("study.links")}
            </Typography>
            <Box
              width="90%"
              display="flex"
              justifyContent="flex-start"
              alignItems="baseline"
              boxSizing="border-box"
              marginBottom="8px"
            >
              <Typography sx={{ fontWeight: "bold", color: "text.secondary" }}>
                {t("study.area1")}
              </Typography>
              <StyledLinkTypo
                variant="body2"
                onClick={() => handleClick(link.source)}
              >
                {link.source}
              </StyledLinkTypo>
            </Box>
            <Box
              width="90%"
              display="flex"
              justifyContent="flex-start"
              alignItems="baseline"
              boxSizing="border-box"
              marginBottom="8px"
            >
              <Typography sx={{ fontWeight: "bold", color: "text.secondary" }}>
                {t("study.area2")}
              </Typography>
              <StyledLinkTypo
                variant="body2"
                onClick={() => handleClick(link.target)}
              >
                {link.target}
              </StyledLinkTypo>
            </Box>
          </Box>
        )}
        <Divider sx={{ height: "1px", width: "90%", mt: 1, mb: 1.5 }} />
        <Box
          width="90%"
          display="flex"
          justifyContent="space-between"
          alignItems="center"
        >
          <Button
            color="primary"
            size="small"
            onClick={() => setSelectedItem(undefined)}
          >
            {t("button.back")}
          </Button>
          <StyledDeleteIcon onClick={() => setOpenConfirmationModal(true)} />
        </Box>
      </Box>
      {openConfirmationModal && (
        <ConfirmationDialog
          onCancel={() => setOpenConfirmationModal(false)}
          onConfirm={() => {
            if (node) {
              onDelete(node.id);
            }
            if (link) {
              onDelete(link.source, link.target);
            }
            setOpenConfirmationModal(false);
          }}
          alert="warning"
          open
        >
          <Typography sx={{ p: 3 }}>
            {node && t("study.question.deleteArea")}
            {link && t("study.question.deleteLink")}
          </Typography>
        </ConfirmationDialog>
      )}
    </>
  );
}

PanelView.defaultProps = {
  nodes: undefined,
  node: undefined,
  links: undefined,
  link: undefined,
};
export default PanelView;
