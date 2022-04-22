import { useState } from "react";
import { Typography, Box, Button } from "@mui/material";
import { useTranslation } from "react-i18next";
import PropertiesView from "../../../common/PropertiesView";
import {
  XpansionCandidate,
  XpansionRenderView,
} from "../../../../common/types";
import CandidateListing from "./CandidateListing";
import BasicModal from "../../../common/BasicModal";

interface PropsType {
  candidateList: Array<XpansionCandidate>;
  selectedItem: string;
  setSelectedItem: (item: string) => void;
  onAdd: () => void;
  deleteXpansion: () => void;
  setView: (item: XpansionRenderView | undefined) => void;
}

function XpansionPropsView(props: PropsType) {
  const [t] = useTranslation();
  const {
    candidateList,
    selectedItem,
    setSelectedItem,
    onAdd,
    deleteXpansion,
    setView,
  } = props;
  const [filteredCandidates, setFilteredCandidates] =
    useState<Array<XpansionCandidate>>();
  const [openConfirmationModal, setOpenConfirmationModal] =
    useState<boolean>(false);

  const filter = (currentName: string): XpansionCandidate[] => {
    if (candidateList) {
      return candidateList.filter(
        (item) =>
          !currentName || item.name.search(new RegExp(currentName, "i")) !== -1
      );
    }
    return [];
  };

  const onChange = async (currentName: string) => {
    if (currentName !== "") {
      const f = filter(currentName);
      setFilteredCandidates(f);
    } else {
      setFilteredCandidates(undefined);
    }
  };

  return (
    <>
      <PropertiesView
        mainContent={
          !filteredCandidates && (
            <Box
              width="100%"
              display="flex"
              flexDirection="column"
              alignItems="flex-end"
              flexGrow={1}
              marginBottom="120px"
            >
              <CandidateListing
                candidates={candidateList}
                selectedItem={selectedItem}
                setSelectedItem={setSelectedItem}
                setView={setView}
              />
              <Box
                sx={{
                  position: "absolute",
                  bottom: "20px",
                  display: "flex",
                  flexDirection: "column",
                  alignItems: "flex-end",
                  color: "secondary.dark",
                }}
              >
                <Button
                  sx={{ color: "primary.main" }}
                  size="small"
                  onClick={() => setView(XpansionRenderView.settings)}
                >
                  {t("main:settings")}
                </Button>
                <Button
                  sx={{ color: "primary.main" }}
                  size="small"
                  onClick={() => setView(XpansionRenderView.files)}
                >
                  {t("main:files")}
                </Button>
                <Button
                  sx={{ color: "primary.main" }}
                  size="small"
                  onClick={() => setView(XpansionRenderView.capacities)}
                >
                  {t("xpansion:capacities")}
                </Button>
                <Button
                  sx={{ color: "error.main" }}
                  size="small"
                  onClick={() => setOpenConfirmationModal(true)}
                >
                  {t("main:delete")}
                </Button>
              </Box>
            </Box>
          )
        }
        secondaryContent={
          filteredCandidates && (
            <Box
              width="90%"
              display="flex"
              flexDirection="column"
              alignItems="center"
              flexGrow={1}
              marginBottom="120px"
            >
              <CandidateListing
                candidates={filteredCandidates}
                selectedItem={selectedItem}
                setSelectedItem={setSelectedItem}
                setView={setView}
              />
              <Box
                sx={{
                  position: "absolute",
                  bottom: "20px",
                  display: "flex",
                  flexDirection: "column",
                  alignItems: "flex-end",
                  color: "secondary.dark",
                }}
              >
                <Button
                  sx={{ color: "primary.main" }}
                  size="small"
                  onClick={() => setView(XpansionRenderView.settings)}
                >
                  {t("main:settings")}
                </Button>
                <Button
                  sx={{ color: "primary.main" }}
                  size="small"
                  onClick={() => setView(XpansionRenderView.files)}
                >
                  {t("main:files")}
                </Button>
                <Button
                  sx={{ color: "primary.main" }}
                  size="small"
                  onClick={() => setView(XpansionRenderView.capacities)}
                >
                  {t("xpansion:capacities")}
                </Button>
                <Button
                  sx={{ color: "error.main" }}
                  size="small"
                  onClick={() => setOpenConfirmationModal(true)}
                >
                  {t("main:delete")}
                </Button>
              </Box>
            </Box>
          )
        }
        onSearchFilterChange={(e) => onChange(e as string)}
        onAdd={onAdd}
      />
      {openConfirmationModal && candidateList && (
        <BasicModal
          open={openConfirmationModal}
          title={t("main:confirmationModalTitle")}
          closeButtonLabel={t("main:noButton")}
          actionButtonLabel={t("main:yesButton")}
          onActionButtonClick={() => {
            deleteXpansion();
            setOpenConfirmationModal(false);
          }}
          onClose={() => setOpenConfirmationModal(false)}
          rootStyle={{
            maxWidth: "800px",
            maxHeight: "800px",
            display: "flex",
            flexFlow: "column nowrap",
            alignItems: "center",
          }}
        >
          <Typography sx={{ p: 3 }}>
            {t("xpansion:confirmDeleteXpansion")}
          </Typography>
        </BasicModal>
      )}
    </>
  );
}

export default XpansionPropsView;
