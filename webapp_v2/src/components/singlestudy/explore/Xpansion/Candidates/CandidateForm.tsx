import { useState, useEffect } from "react";
import { Box, Divider, Typography, Button, ButtonGroup } from "@mui/material";
import { useTranslation } from "react-i18next";
import SaveIcon from "@mui/icons-material/Save";
import VisibilityIcon from "@mui/icons-material/Visibility";
import DeleteIcon from "@mui/icons-material/Delete";
import ConfirmationDialog from "../../../../common/dialogs/ConfirmationDialog";
import { Title, Fields, SelectFields, StyledTextField } from "../Styles";
import {
  XpansionCandidate,
  LinkCreationInfo,
} from "../../../../../common/types";
import SelectSingle from "../../../../common/SelectSingle";

interface PropType {
  candidate: XpansionCandidate;
  links: Array<LinkCreationInfo>;
  capacities: Array<string>;
  deleteCandidate: (name: string) => Promise<void>;
  updateCandidate: (name: string, value: XpansionCandidate) => Promise<void>;
  onRead: (filename: string) => Promise<void>;
}

function CandidateForm(props: PropType) {
  const [t] = useTranslation();
  const {
    candidate,
    links,
    capacities,
    deleteCandidate,
    updateCandidate,
    onRead,
  } = props;
  const [openConfirmationModal, setOpenConfirmationModal] =
    useState<boolean>(false);
  const [currentCandidate, setCurrentCandidate] =
    useState<XpansionCandidate>(candidate);
  const [saveAllowed, setSaveAllowed] = useState<boolean>(false);
  const [toggleView, setToggleView] = useState<boolean>(true);

  const tabLinks = links.map((item) => {
    return {
      id: `${item.area1} - ${item.area2}`,
      name: `${item.area1} - ${item.area2}`,
    };
  });

  const handleChange = (key: string, value: string | number) => {
    setSaveAllowed(true);
    setCurrentCandidate({ ...currentCandidate, [key]: value });
  };

  const changeView = () => setToggleView(!toggleView);

  useEffect(() => {
    if (candidate) {
      setCurrentCandidate(candidate);
      setSaveAllowed(false);
      if (candidate["max-investment"] && candidate["max-investment"] >= 0) {
        setToggleView(false);
      } else {
        setToggleView(true);
      }
    }
  }, [candidate]);

  return (
    <Box>
      <Box>
        <Box
          display="flex"
          justifyContent="space-between"
          alignItems="flex-end"
        >
          <Title>{t("main:general")}</Title>
          <Box
            display="flex"
            justifyContent="space-between"
            alignItems="center"
          >
            <Button
              variant="outlined"
              color="primary"
              sx={{
                display: "flex",
                flexFlow: "row nowrap",
                justifyContent: "space-between",
                alignItems: "center",
                height: "30px",
                mr: 1,
                border: "2px solid",
              }}
              onClick={() => {
                updateCandidate(currentCandidate.name, currentCandidate);
                setSaveAllowed(false);
              }}
              disabled={!saveAllowed}
            >
              <SaveIcon sx={{ m: 0.2, width: "16px", height: "16px" }} />
              <Typography sx={{ m: 0.2, fontSize: "12px" }}>
                {t("main:save")}
              </Typography>
            </Button>
            <DeleteIcon
              sx={{
                cursor: "pointer",
                color: "error.light",
                "&:hover": {
                  color: "error.main",
                },
              }}
              onClick={() => setOpenConfirmationModal(true)}
            />
          </Box>
        </Box>
        <Divider sx={{ mt: 1, mb: 2 }} />
        <Fields>
          <StyledTextField
            label={t("main:name")}
            variant="filled"
            value={currentCandidate.name}
            onChange={(e) => handleChange("name", e.target.value)}
          />
          <SelectFields>
            <SelectSingle
              name={t("xpansion:link")}
              label="link"
              list={tabLinks}
              data={currentCandidate.link}
              handleChange={handleChange}
              sx={{
                minWidth: "100%",
              }}
            />
          </SelectFields>
        </Fields>
      </Box>
      <Box>
        <Title>{t("main:settings")}</Title>
        <Divider sx={{ mt: 1, mb: 2 }} />
        <Fields>
          <StyledTextField
            type="number"
            label={t("xpansion:annualCost")}
            variant="filled"
            value={currentCandidate["annual-cost-per-mw"] || ""}
            onChange={(e) =>
              handleChange("annual-cost-per-mw", parseFloat(e.target.value))
            }
          />
          <StyledTextField
            type="number"
            label={t("xpansion:alreadyICapacity")}
            variant="filled"
            value={currentCandidate["already-installed-capacity"] || ""}
            onChange={(e) =>
              handleChange(
                "already-installed-capacity",
                parseFloat(e.target.value)
              )
            }
          />
        </Fields>
        <Fields>
          <Box
            width="100% !important"
            display="flex"
            justifyContent="flex-start"
          >
            <ButtonGroup sx={{ width: "270px", mb: 2 }} variant="outlined">
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
              <StyledTextField
                sx={{ mr: 2 }}
                type="number"
                label={t("xpansion:unitSize")}
                variant="filled"
                value={currentCandidate["unit-size"] || ""}
                onChange={(e) =>
                  handleChange("unit-size", parseFloat(e.target.value))
                }
              />
              <StyledTextField
                type="number"
                label={t("xpansion:maxUnits")}
                variant="filled"
                value={currentCandidate["max-units"] || ""}
                onChange={(e) =>
                  handleChange("max-units", parseFloat(e.target.value))
                }
              />
            </>
          )}
          {!toggleView && (
            <StyledTextField
              type="number"
              label={t("xpansion:maxInvestments")}
              variant="filled"
              value={currentCandidate["max-investment"] || ""}
              onChange={(e) =>
                handleChange("max-investment", parseFloat(e.target.value))
              }
            />
          )}
        </Fields>
      </Box>
      <Box>
        <Title>{t("xpansion:timeSeries")}</Title>
        <Divider sx={{ mt: 1, mb: 2 }} />
        <Box
          sx={{
            display: "flex",
            flexDirection: "column",
            alignItems: "flex-start",
            width: "100%",
            mb: 2,
            "&> div": {
              mr: 2,
              mb: 2,
            },
          }}
        >
          <SelectFields>
            <SelectSingle
              name={t("xpansion:linkProfile")}
              label="link-profile"
              list={capacities.map((item) => {
                return { id: item, name: item };
              })}
              data={currentCandidate["link-profile"] || ""}
              handleChange={handleChange}
              sx={{
                minWidth: "100%",
              }}
              optional
            />
            <VisibilityIcon
              sx={{
                mx: 1,
                color: "action.active",
                "&:hover": {
                  color: "primary.main",
                  cursor: "pointer",
                },
              }}
              onClick={() =>
                currentCandidate["link-profile"] &&
                onRead(currentCandidate["link-profile"] || "")
              }
            />
          </SelectFields>
          <SelectFields>
            <SelectSingle
              name={t("xpansion:alreadyILinkProfile")}
              label="already-installed-link-profile"
              list={capacities.map((item) => {
                return { id: item, name: item };
              })}
              data={currentCandidate["already-installed-link-profile"] || ""}
              handleChange={handleChange}
              sx={{
                minWidth: "100%",
              }}
              optional
            />
            <VisibilityIcon
              sx={{
                mx: 1,
                color: "action.active",
                "&:hover": {
                  color: "primary.main",
                  cursor: "pointer",
                },
              }}
              color="primary"
              onClick={() =>
                currentCandidate["already-installed-link-profile"] &&
                onRead(currentCandidate["already-installed-link-profile"] || "")
              }
            />
          </SelectFields>
        </Box>
      </Box>
      {openConfirmationModal && candidate && (
        <ConfirmationDialog
          titleIcon={DeleteIcon}
          onCancel={() => setOpenConfirmationModal(false)}
          onConfirm={() => {
            deleteCandidate(currentCandidate.name);
            setOpenConfirmationModal(false);
          }}
          alert="warning"
          open
        >
          Êtes-vous sûr de vouloir supprimer ce candidat?
        </ConfirmationDialog>
      )}
    </Box>
  );
}

export default CandidateForm;
