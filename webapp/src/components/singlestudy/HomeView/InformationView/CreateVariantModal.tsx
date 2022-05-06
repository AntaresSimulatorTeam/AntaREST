import { useEffect, useState } from "react";
import { useSnackbar } from "notistack";
import { useNavigate } from "react-router";
import { Box } from "@mui/material";
import { useTranslation } from "react-i18next";
import { AxiosError } from "axios";
import BasicModal from "../../../common/BasicModal";
import FilledTextInput from "../../../common/FilledTextInput";
import SingleSelect from "../../../common/SelectSingle";
import { GenericInfo, VariantTree } from "../../../../common/types";
import { scrollbarStyle } from "../../../../theme";
import { createVariant } from "../../../../services/api/variant";
import { createListFromTree } from "../../../../services/utils";
import useEnqueueErrorSnackbar from "../../../../hooks/useEnqueueErrorSnackbar";

interface Props {
  open: boolean;
  parentId: string;
  tree: VariantTree;
  onClose: () => void;
}

function CreateVariantModal(props: Props) {
  const [t] = useTranslation();
  const { open, parentId, tree, onClose } = props;
  const navigate = useNavigate();
  const { enqueueSnackbar } = useSnackbar();
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();
  const [studyName, setStudyName] = useState<string>("");
  const [versionSourceList, setVersionSourceList] = useState<
    Array<GenericInfo>
  >([]);
  const [versionSource, setVersionSource] = useState<string>(parentId);

  const onSave = async () => {
    if (!studyName) {
      enqueueSnackbar(t("variants:nameEmptyError"), { variant: "error" });
      return;
    }
    try {
      const newId = await createVariant(versionSource, studyName);
      setStudyName("");
      onClose();
      navigate(`/studies/${newId}`);
    } catch (e) {
      enqueueErrorSnackbar(
        t("variants:onVariantCreationError"),
        e as AxiosError
      );
    }
  };

  useEffect(() => {
    setVersionSourceList(createListFromTree(tree));
  }, [tree]);

  return (
    <BasicModal
      title={t("studymanager:createNewStudy")}
      open={open}
      onClose={onClose}
      closeButtonLabel={t("main:cancelButton")}
      actionButtonLabel={t("main:create")}
      onActionButtonClick={onSave}
      rootStyle={{
        width: "600px",
        display: "flex",
        flexDirection: "column",
        justifyContent: "flex-start",
        alignItems: "center",
        boxSizing: "border-box",
      }}
    >
      <Box
        width="100%"
        height="180px"
        display="flex"
        flexDirection="column"
        justifyContent="flex-start"
        alignItems="center"
        p={2}
        boxSizing="border-box"
        sx={{ overflowX: "hidden", overflowY: "auto", ...scrollbarStyle }}
      >
        <Box
          width="100%"
          display="flex"
          flexDirection="row"
          justifyContent="flex-start"
          alignItems="center"
          boxSizing="border-box"
        >
          <FilledTextInput
            label={`${t("variants:newVariant")} *`}
            value={studyName}
            onChange={setStudyName}
            sx={{ flexGrow: 1 }}
          />
        </Box>
        <Box
          width="100%"
          display="flex"
          flexDirection="row"
          justifyContent="flex-start"
          alignItems="center"
          boxSizing="border-box"
          mt={3}
        >
          <SingleSelect
            name={`${t("singlestudy:versionSource")} *`}
            label={t("singlestudy:versionSource")}
            list={versionSourceList}
            data={versionSource}
            setValue={(data: string) => setVersionSource(data)}
            sx={{ flexGrow: 1 }}
          />
        </Box>
      </Box>
    </BasicModal>
  );
}

export default CreateVariantModal;
