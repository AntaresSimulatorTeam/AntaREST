import { useState, useEffect } from "react";
import {
  Box,
  Divider,
  Typography,
  Button,
  ButtonGroup,
  Paper,
  TextField,
} from "@mui/material";
import { useTranslation } from "react-i18next";
import SaveIcon from "@mui/icons-material/Save";
import DeleteIcon from "@mui/icons-material/Delete";
import ConfirmationDialog from "../../../../../common/dialogs/ConfirmationDialog";
import {
  Title,
  Fields,
  SelectFields,
  HoverButton,
  ActiveButton,
  StyledVisibilityIcon,
  StyledDeleteIcon,
} from "../share/styles";
import { LinkCreationInfoDTO } from "../../../../../../common/types";
import { XpansionCandidate } from "../types";
import SelectSingle from "../../../../../common/SelectSingle";
import SwitchFE from "../../../../../common/fieldEditors/SwitchFE";

interface PropType {
  candidate: XpansionCandidate | undefined;
  links: Array<LinkCreationInfoDTO>;
  capacities: Array<string>;
  deleteCandidate: (name: string | undefined) => Promise<void>;
  updateCandidate: (
    name: string | undefined,
    value: XpansionCandidate | undefined
  ) => Promise<void>;
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
  const [currentCandidate, setCurrentCandidate] = useState<
    XpansionCandidate | undefined
  >(candidate);
  const [saveAllowed, setSaveAllowed] = useState<boolean>(false);
  const [toggleView, setToggleView] = useState<boolean>(true);
  const [useV8LinkProfile, setUseV8LinkProfile] = useState<boolean>(true);

  const tabLinks = links.map((item) => {
    return {
      id: `${item.area1} - ${item.area2}`,
      name: `${item.area1} - ${item.area2}`,
    };
  });

  const handleChange = (key: string, value: string | number) => {
    setSaveAllowed(true);
    if (currentCandidate) {
      setCurrentCandidate({ ...currentCandidate, [key]: value });
    }
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
    <Paper sx={{ width: "100%", height: "100%", overflow: "auto", p: 2 }}>
      <Box>
        <Box
          display="flex"
          justifyContent="space-between"
          alignItems="flex-end"
        >
          <Title>{t("global.general")}</Title>
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
                updateCandidate(candidate?.name, currentCandidate);
                setSaveAllowed(false);
              }}
              disabled={!saveAllowed}
            >
              <SaveIcon sx={{ m: 0.2, width: "16px", height: "16px" }} />
              <Typography sx={{ m: 0.2, fontSize: "12px" }}>
                {t("global.save")}
              </Typography>
            </Button>
            <StyledDeleteIcon onClick={() => setOpenConfirmationModal(true)} />
          </Box>
        </Box>
        <Divider sx={{ mt: 1, mb: 2 }} />
        <Fields>
          <TextField
            label={t("global.name")}
            variant="filled"
            value={currentCandidate?.name || ""}
            onChange={(e) => handleChange("name", e.target.value)}
          />
          <SelectFields>
            <SelectSingle
              name="link"
              label={t("xpansion.link")}
              list={tabLinks}
              data={currentCandidate?.link || ""}
              handleChange={handleChange}
              sx={{
                minWidth: "100%",
              }}
            />
          </SelectFields>
        </Fields>
      </Box>
      <Box>
        <Title>{t("global.settings")}</Title>
        <Divider sx={{ mt: 1, mb: 2 }} />
        <Fields>
          <TextField
            type="number"
            label={t("xpansion.annualCost")}
            variant="filled"
            value={currentCandidate?.["annual-cost-per-mw"] || ""}
            onChange={(e) =>
              handleChange("annual-cost-per-mw", parseFloat(e.target.value))
            }
          />
          <TextField
            type="number"
            label={t("xpansion.alreadyICapacity")}
            variant="filled"
            value={currentCandidate?.["already-installed-capacity"] || ""}
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
            <ButtonGroup sx={{ mb: 2 }} size="small">
              {toggleView ? (
                <ActiveButton variant="outlined" disabled>
                  {`${t("xpansion.unitSize")} & ${t("xpansion.maxUnits")}`}
                </ActiveButton>
              ) : (
                <HoverButton variant="outlined" onClick={changeView}>
                  {`${t("xpansion.unitSize")} & ${t("xpansion.maxUnits")}`}
                </HoverButton>
              )}
              {toggleView ? (
                <HoverButton variant="outlined" onClick={changeView}>
                  {t("xpansion.maxInvestments")}
                </HoverButton>
              ) : (
                <ActiveButton variant="outlined" disabled>
                  {t("xpansion.maxInvestments")}
                </ActiveButton>
              )}
            </ButtonGroup>
          </Box>
          {toggleView && (
            <>
              <TextField
                sx={{ mr: 2 }}
                type="number"
                label={t("xpansion.unitSize")}
                variant="filled"
                value={currentCandidate?.["unit-size"] || ""}
                onChange={(e) =>
                  handleChange("unit-size", parseFloat(e.target.value))
                }
              />
              <TextField
                type="number"
                label={t("xpansion.maxUnits")}
                variant="filled"
                value={currentCandidate?.["max-units"] || ""}
                onChange={(e) =>
                  handleChange("max-units", parseFloat(e.target.value))
                }
              />
            </>
          )}
          {!toggleView && (
            <TextField
              type="number"
              label={t("xpansion.maxInvestments")}
              variant="filled"
              value={currentCandidate?.["max-investment"] || ""}
              onChange={(e) =>
                handleChange("max-investment", parseFloat(e.target.value))
              }
            />
          )}
        </Fields>
      </Box>
      <Box>
        <Title>{t("xpansion.timeSeries")}</Title>
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
          <SwitchFE
            value={useV8LinkProfile}
            onChange={() => setUseV8LinkProfile((before) => !before)}
            label="v8"
          />
          {useV8LinkProfile ? (
            <>
              <Box sx={{ display: "flex", width: "100%" }}>
                <SelectFields>
                  <SelectSingle
                    name="direct-link-profile"
                    label={t("xpansion.directLinkProfile")}
                    list={capacities.map((item) => {
                      return { id: item, name: item };
                    })}
                    data={currentCandidate?.["direct-link-profile"] || ""}
                    handleChange={handleChange}
                    sx={{
                      minWidth: "100%",
                    }}
                    optional
                  />
                  <StyledVisibilityIcon
                    onClick={() =>
                      currentCandidate?.["direct-link-profile"] &&
                      onRead(currentCandidate?.["direct-link-profile"] || "")
                    }
                  />
                </SelectFields>
                <SelectFields>
                  <SelectSingle
                    name="indirect-link-profile"
                    label={t("xpansion.indirectLinkProfile")}
                    list={capacities.map((item) => {
                      return { id: item, name: item };
                    })}
                    data={currentCandidate?.["indirect-link-profile"] || ""}
                    handleChange={handleChange}
                    sx={{
                      minWidth: "100%",
                    }}
                    optional
                  />
                  <StyledVisibilityIcon
                    onClick={() =>
                      currentCandidate?.["indirect-link-profile"] &&
                      onRead(currentCandidate?.["indirect-link-profile"] || "")
                    }
                  />
                </SelectFields>
              </Box>
              <Box sx={{ display: "flex", width: "100%" }}>
                <SelectFields>
                  <SelectSingle
                    name="direct-already-installed-link-profile"
                    label={t("xpansion.directAlreadyLinkProfile")}
                    list={capacities.map((item) => {
                      return { id: item, name: item };
                    })}
                    data={
                      currentCandidate?.[
                        "direct-already-installed-link-profile"
                      ] || ""
                    }
                    handleChange={handleChange}
                    sx={{
                      minWidth: "100%",
                    }}
                    optional
                  />
                  <StyledVisibilityIcon
                    onClick={() =>
                      currentCandidate?.[
                        "direct-already-installed-link-profile"
                      ] &&
                      onRead(
                        currentCandidate?.[
                          "direct-already-installed-link-profile"
                        ] || ""
                      )
                    }
                  />
                </SelectFields>
                <SelectFields>
                  <SelectSingle
                    name="indirect-already-installed-link-profile"
                    label={t("xpansion.indirectAlreadyLinkProfile")}
                    list={capacities.map((item) => {
                      return { id: item, name: item };
                    })}
                    data={
                      currentCandidate?.[
                        "indirect-already-installed-link-profile"
                      ] || ""
                    }
                    handleChange={handleChange}
                    sx={{
                      minWidth: "100%",
                    }}
                    optional
                  />
                  <StyledVisibilityIcon
                    onClick={() =>
                      currentCandidate?.[
                        "indirect-already-installed-link-profile"
                      ] &&
                      onRead(
                        currentCandidate?.[
                          "indirect-already-installed-link-profile"
                        ] || ""
                      )
                    }
                  />
                </SelectFields>
              </Box>
            </>
          ) : (
            <>
              <SelectFields>
                <SelectSingle
                  name="link-profile"
                  label={t("xpansion.linkProfile")}
                  list={capacities.map((item) => {
                    return { id: item, name: item };
                  })}
                  data={currentCandidate?.["link-profile"] || ""}
                  handleChange={handleChange}
                  sx={{
                    minWidth: "100%",
                  }}
                  optional
                />
                <StyledVisibilityIcon
                  onClick={() =>
                    currentCandidate?.["link-profile"] &&
                    onRead(currentCandidate?.["link-profile"] || "")
                  }
                />
              </SelectFields>
              <SelectFields>
                <SelectSingle
                  name="already-installed-link-profile"
                  label={t("xpansion.alreadyILinkProfile")}
                  list={capacities.map((item) => {
                    return { id: item, name: item };
                  })}
                  data={
                    currentCandidate?.["already-installed-link-profile"] || ""
                  }
                  handleChange={handleChange}
                  sx={{
                    minWidth: "100%",
                  }}
                  optional
                />
                <StyledVisibilityIcon
                  onClick={() =>
                    currentCandidate?.["already-installed-link-profile"] &&
                    onRead(
                      currentCandidate?.["already-installed-link-profile"] || ""
                    )
                  }
                />
              </SelectFields>
            </>
          )}
        </Box>
      </Box>
      {openConfirmationModal && candidate && (
        <ConfirmationDialog
          titleIcon={DeleteIcon}
          onCancel={() => setOpenConfirmationModal(false)}
          onConfirm={() => {
            deleteCandidate(currentCandidate?.name);
            setOpenConfirmationModal(false);
          }}
          alert="warning"
          open
        >
          {t("xpansion.question.deleteCandidate")}
        </ConfirmationDialog>
      )}
    </Paper>
  );
}

export default CandidateForm;
