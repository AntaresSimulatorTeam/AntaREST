import { useState } from "react";
import { TextField, Button, Box, Divider, ButtonGroup } from "@mui/material";
import { useTranslation } from "react-i18next";
import { LinkCreationInfo } from "../../../../../common/types";
import { XpansionCandidate } from "../types";
import SelectSingle from "../../../../common/SelectSingle";
import { HoverButton, ActiveButton } from "../styles";
import BasicDialog from "../../../../common/dialogs/BasicDialog";

interface PropType {
  open: boolean;
  links: Array<LinkCreationInfo>;
  onClose: () => void;
  onSave: (candidate: XpansionCandidate) => void;
}

function CreateCandidateDialog(props: PropType) {
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
    <BasicDialog
      open={open}
      onClose={onClose}
      title={t("xpansion:newCandidate")}
      contentProps={{
        sx: { width: "auto", height: "480px", p: 2 },
      }}
      actions={
        <>
          <Button variant="text" color="primary" onClick={onClose}>
            {t("main:cancelButton")}
          </Button>
          <Button
            sx={{ mx: 2 }}
            color="primary"
            variant="contained"
            onClick={() => onSave(candidate)}
          >
            {t("data:saveButton")}
          </Button>
        </>
      }
    >
      <Box
        sx={{
          width: "280px",
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
        />
        <SelectSingle
          name="link"
          label={t("xpansion:link")}
          list={tabLinks.map((item) => {
            return { id: item, name: item };
          })}
          data={candidate.link}
          handleChange={handleChange}
          variant="outlined"
          sx={{ m: 1, width: "234px" }}
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
            sx={{ width: "234px", display: "flex", justifyContent: "center" }}
            variant="outlined"
          >
            {toggleView ? (
              <ActiveButton size="small" variant="outlined" disabled>
                {`${t("xpansion:unitSize")} & ${t("xpansion:maxUnits")}`}
              </ActiveButton>
            ) : (
              <HoverButton size="small" variant="outlined" onClick={changeView}>
                {`${t("xpansion:unitSize")} & ${t("xpansion:maxUnits")}`}
              </HoverButton>
            )}
            {toggleView ? (
              <HoverButton size="small" variant="outlined" onClick={changeView}>
                {t("xpansion:maxInvestments")}
              </HoverButton>
            ) : (
              <ActiveButton size="small" variant="outlined" disabled>
                {t("xpansion:maxInvestments")}
              </ActiveButton>
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
    </BasicDialog>
  );
}

export default CreateCandidateDialog;
