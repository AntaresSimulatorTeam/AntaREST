import { useState } from "react";
import { TextField, Box, Divider, ButtonGroup, Button } from "@mui/material";
import { useTranslation } from "react-i18next";
import BasicModal from "../../../../common/BasicModal";
import {
  LinkCreationInfo,
  XpansionCandidate,
} from "../../../../../common/types";
import SelectSingle from "../../../../common/SelectSingle";

interface PropType {
  open: boolean;
  links: Array<LinkCreationInfo>;
  onClose: () => void;
  onSave: (candidate: XpansionCandidate) => void;
}

function CreateCandidateModal(props: PropType) {
  const [t] = useTranslation();
  const { open, links, onClose, onSave } = props;
  const [candidate, setCandidate] = useState<XpansionCandidate>({
    name: "",
    link: "",
    "annual-cost-per-mw": 0,
  });
  const [toggleView, setToggleView] = useState<boolean>(true);

  const tabLinks = links.map((item) => `${item.area1} - ${item.area2}`);

  const handleChange = (key: string, value: string | number) => {
    setCandidate({ ...candidate, [key]: value });
  };

  const changeView = () => setToggleView(!toggleView);

  return (
    <BasicModal
      open={open}
      onClose={onClose}
      closeButtonLabel={t("settings:cancelButton")}
      actionButtonLabel={t("settings:saveButton")}
      onActionButtonClick={() => onSave(candidate)}
      title={t("xpansion:newCandidate")}
      rootStyle={{
        maxWidth: "80%",
        maxHeight: "70%",
        display: "flex",
        flexFlow: "column nowrap",
        alignItems: "center",
      }}
    >
      <Box
        sx={{
          width: "250px",
          m: 2,
          display: "flex",
          flexDirection: "column",
          alignItems: "flex-start",
          "& > div": {
            mb: 1,
          },
          "&> svg": {
            mb: 1,
          },
        }}
      >
        <TextField
          label={t("main:name")}
          variant="outlined"
          onChange={(e) => handleChange("name", e.target.value)}
          value={candidate.name}
          size="small"
        />
        <SelectSingle
          name={t("xpansion:link")}
          label="link"
          list={tabLinks.map((item) => {
            return { id: item, name: item };
          })}
          data={candidate.link}
          handleChange={handleChange}
          variant="outlined"
        />
        <TextField
          type="number"
          label={t("xpansion:annualCost")}
          variant="outlined"
          value={candidate["annual-cost-per-mw"] || ""}
          onChange={(e) =>
            handleChange("annual-cost-per-mw", parseFloat(e.target.value))
          }
        />
        <Divider
          sx={{
            width: "100%",
            mt: 1,
            mb: 2,
          }}
        />
        <Box width="100%" display="flex" justifyContent="center">
          <ButtonGroup
            sx={{ width: "100%", display: "flex", justifyContent: "center" }}
            variant="outlined"
          >
            {toggleView ? (
              <Button
                size="small"
                variant="outlined"
                disabled
                sx={(theme) => ({
                  backgroundColor: `${theme.palette.primary.main} !important`,
                  color: `${theme.palette.primary.contrast} !important`,
                })}
              >
                {`${t("xpansion:unitSize")} & ${t("xpansion:maxUnits")}`}
              </Button>
            ) : (
              <Button
                size="small"
                variant="outlined"
                sx={(theme) => ({
                  color: "action.active",
                  "&:hover": {
                    backgroundColor: theme.palette.primary.main,
                    color: theme.palette.primary.contrast,
                  },
                })}
                onClick={changeView}
              >
                {`${t("xpansion:unitSize")} & ${t("xpansion:maxUnits")}`}
              </Button>
            )}
            {toggleView ? (
              <Button
                size="small"
                variant="outlined"
                sx={(theme) => ({
                  color: "action.active",
                  "&:hover": {
                    backgroundColor: theme.palette.primary.main,
                    color: theme.palette.primary.contrast,
                  },
                })}
                onClick={changeView}
              >
                {t("xpansion:maxInvestments")}
              </Button>
            ) : (
              <Button
                size="small"
                variant="outlined"
                sx={(theme) => ({
                  backgroundColor: `${theme.palette.primary.main} !important`,
                  color: `${theme.palette.primary.contrast} !important`,
                })}
                disabled
              >
                {t("xpansion:maxInvestments")}
              </Button>
            )}
          </ButtonGroup>
        </Box>
        {toggleView && (
          <>
            <TextField
              type="number"
              label={t("xpansion:unitSize")}
              variant="outlined"
              value={candidate["unit-size"] || ""}
              onChange={(e) =>
                handleChange("unit-size", parseFloat(e.target.value))
              }
            />
            <TextField
              type="number"
              label={t("xpansion:maxUnits")}
              variant="outlined"
              value={candidate["max-units"] || ""}
              onChange={(e) =>
                handleChange("max-units", parseFloat(e.target.value))
              }
            />
          </>
        )}
        {!toggleView && (
          <TextField
            type="number"
            label={t("xpansion:maxInvestments")}
            variant="outlined"
            value={candidate["max-investment"] || ""}
            onChange={(e) =>
              handleChange("max-investment", parseFloat(e.target.value))
            }
          />
        )}
      </Box>
    </BasicModal>
  );
}

export default CreateCandidateModal;
