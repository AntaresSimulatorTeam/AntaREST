import { useCallback, useEffect, useState } from "react";
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
    useState<Array<XpansionCandidate>>(candidateList);
  const [searchFilter, setSearchFilter] = useState<string>("");
  const [openConfirmationModal, setOpenConfirmationModal] =
    useState<boolean>(false);

  const filter = useCallback(
    (currentName: string): XpansionCandidate[] => {
      if (candidateList) {
        return candidateList.filter(
          (item) =>
            !currentName ||
            item.name.search(new RegExp(currentName, "i")) !== -1
        );
      }
      return [];
    },
    [candidateList]
  );

  useEffect(() => {
    setFilteredCandidates(filter(searchFilter));
  }, [filter, searchFilter]);

  return (
    <>
      <PropertiesView
        mainContent={
          <ListElement
            list={filteredCandidates}
            currentElement={selectedItem}
            setSelectedItem={(elm) => setSelectedItem(elm.name)}
          />
        }
        secondaryContent={
          <Box
            sx={{
              position: "absolute",
              bottom: "24px",
              right: "24px",
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
        }
        onSearchFilterChange={setSearchFilter}
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
