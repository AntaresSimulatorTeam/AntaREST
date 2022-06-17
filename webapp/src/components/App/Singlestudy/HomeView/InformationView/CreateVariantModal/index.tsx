import { useEffect, useState } from "react";
import { useSnackbar } from "notistack";
import { useNavigate } from "react-router";
import { Button, TextField } from "@mui/material";
import { useTranslation } from "react-i18next";
import { AxiosError } from "axios";
import SingleSelect from "../../../../../common/SelectSingle";
import { GenericInfo, VariantTree } from "../../../../../../common/types";
import { createVariant } from "../../../../../../services/api/variant";
import { createListFromTree } from "../../../../../../services/utils";
import useEnqueueErrorSnackbar from "../../../../../../hooks/useEnqueueErrorSnackbar";
import BasicDialog from "../../../../../common/dialogs/BasicDialog";
import { InputContainer, Root } from "./style";

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
      enqueueSnackbar(t("variants.error.nameEmpty"), {
        variant: "error",
      });
      return;
    }
    try {
      const newId = await createVariant(versionSource, studyName);
      setStudyName("");
      onClose();
      navigate(`/studies/${newId}`);
    } catch (e) {
      enqueueErrorSnackbar(
        t("variants.error.variantCreation"),
        e as AxiosError
      );
    }
  };

  useEffect(() => {
    setVersionSourceList(createListFromTree(tree));
  }, [tree]);

  return (
    <BasicDialog
      open={open}
      onClose={onClose}
      title={t("studies.createNewStudy")}
      actions={
        <>
          <Button variant="text" color="primary" onClick={onClose}>
            {t("global.cancel")}
          </Button>
          <Button
            sx={{ mx: 2 }}
            color="primary"
            variant="contained"
            onClick={onSave}
          >
            {t("global.create")}
          </Button>
        </>
      }
    >
      <Root>
        <InputContainer>
          <TextField
            label={t("variants.newVariant")}
            value={studyName}
            onChange={(ev) => setStudyName(ev.target.value)}
            sx={{ flexGrow: 1 }}
            variant="filled"
            required
          />
        </InputContainer>
        <InputContainer mt={3}>
          <SingleSelect
            name={t("study.versionSource")}
            list={versionSourceList}
            data={versionSource}
            setValue={(data: string) => setVersionSource(data)}
            sx={{ flexGrow: 1 }}
            required
          />
        </InputContainer>
      </Root>
    </BasicDialog>
  );
}

export default CreateVariantModal;
