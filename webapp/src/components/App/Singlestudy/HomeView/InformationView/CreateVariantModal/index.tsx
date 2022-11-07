import { useEffect, useState } from "react";
import { useNavigate } from "react-router";
import { useTranslation } from "react-i18next";
import { AxiosError } from "axios";
import AddCircleIcon from "@mui/icons-material/AddCircle";
import { GenericInfo, VariantTree } from "../../../../../../common/types";
import { createVariant } from "../../../../../../services/api/variant";
import { createListFromTree } from "../../../../../../services/utils";
import useEnqueueErrorSnackbar from "../../../../../../hooks/useEnqueueErrorSnackbar";
import FormDialog from "../../../../../common/dialogs/FormDialog";
import StringFE from "../../../../../common/fieldEditors/StringFE";
import Fieldset from "../../../../../common/Fieldset";
import SelectFE from "../../../../../common/fieldEditors/SelectFE";
import { SubmitHandlerPlus } from "../../../../../common/Form";

interface Props {
  parentId: string;
  open: boolean;
  tree: VariantTree;
  onClose: () => void;
}

function CreateVariantModal(props: Props) {
  const { parentId, open, tree, onClose } = props;
  const [t] = useTranslation();
  const navigate = useNavigate();
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();
  const [sourceList, setSourceList] = useState<Array<GenericInfo>>([]);

  useEffect(() => {
    setSourceList(createListFromTree(tree));
  }, [tree]);

  const defaultValues = {
    name: "",
    sourceId: parentId,
  };

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleSubmit = async (
    data: SubmitHandlerPlus<typeof defaultValues>
  ) => {
    const { sourceId, name } = data.values;

    try {
      if (sourceId) {
        const variantId = await createVariant(sourceId, name);
        onClose();
        navigate(`/studies/${variantId}`);
      }
    } catch (e) {
      enqueueErrorSnackbar(
        t("variants.error.variantCreation"),
        e as AxiosError
      );
    }
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <FormDialog
      title={t("studies.createNewStudy")}
      titleIcon={AddCircleIcon}
      open={open}
      onCancel={onClose}
      onSubmit={handleSubmit}
      config={{ defaultValues }}
    >
      {({ control }) => (
        <Fieldset fullFieldWidth>
          <StringFE
            label={t("variants.newVariant")}
            name="name"
            control={control}
            rules={{
              required: true,
              validate: (val) => val.trim().length > 0,
            }}
          />
          <SelectFE
            label={t("study.versionSource")}
            options={sourceList.map((ver) => ({
              label: ver.name,
              value: ver.id,
            }))}
            name="sourceId"
            control={control}
            required
          />
        </Fieldset>
      )}
    </FormDialog>
  );
}

export default CreateVariantModal;
