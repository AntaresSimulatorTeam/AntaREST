import { useState } from "react";
import { Box, Button } from "@mui/material";
import { useTranslation } from "react-i18next";
import DeleteIcon from "@mui/icons-material/Delete";
import PropertiesView from "../../../../../common/PropertiesView";
import { XpansionCandidate } from "../types";
import ConfirmationDialog from "../../../../../common/dialogs/ConfirmationDialog";
import ListElement from "../../common/ListElement";

interface PropsType {
  candidateList: Array<XpansionCandidate>;
  selectedItem: string;
  setSelectedItem: (item: string) => void;
  onAdd: () => void;
  deleteXpansion: () => void;
}

function XpansionPropsView(props: PropsType) {
  const [t] = useTranslation();
  const {
    candidateList,
    selectedItem,
    setSelectedItem,
    onAdd,
    deleteXpansion,
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
            >
              <ListElement
                list={candidateList}
                currentElement={selectedItem}
                setSelectedItem={(elm) => setSelectedItem(elm.name)}
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
                  sx={{ color: "error.light" }}
                  size="small"
                  onClick={() => setOpenConfirmationModal(true)}
                >
                  {t("global.delete")}
                </Button>
              </Box>
            </Box>
          )
        }
        secondaryContent={
          filteredCandidates && (
            <Box
              width="100%"
              display="flex"
              flexDirection="column"
              alignItems="flex-end"
              flexGrow={1}
            >
              <ListElement
                list={filteredCandidates}
                currentElement={selectedItem}
                setSelectedItem={(elm) => setSelectedItem(elm.name)}
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
                  sx={{ color: "error.light" }}
                  size="small"
                  onClick={() => setOpenConfirmationModal(true)}
                >
                  {t("global.delete")}
                </Button>
              </Box>
            </Box>
          )
        }
        onSearchFilterChange={(e) => onChange(e as string)}
        onAdd={onAdd}
      />
      {openConfirmationModal && candidateList && (
        <ConfirmationDialog
          open
          titleIcon={DeleteIcon}
          onConfirm={() => {
            deleteXpansion();
            setOpenConfirmationModal(false);
          }}
          onCancel={() => setOpenConfirmationModal(false)}
          alert="warning"
        >
          {t("xpansion.question.deleteConfiguration")}
        </ConfirmationDialog>
      )}
    </>
  );
}

export default XpansionPropsView;
