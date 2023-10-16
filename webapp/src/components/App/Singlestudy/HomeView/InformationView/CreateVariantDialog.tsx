import { useEffect, useState } from "react";
import { useNavigate } from "react-router";
import { useTranslation } from "react-i18next";
import AddCircleIcon from "@mui/icons-material/AddCircle";
import { GenericInfo, VariantTree } from "../../../../../common/types";
import { createVariant } from "../../../../../services/api/variant";
import { createListFromTree } from "../../../../../services/utils";
import FormDialog from "../../../../common/dialogs/FormDialog";
import StringFE from "../../../../common/fieldEditors/StringFE";
import Fieldset from "../../../../common/Fieldset";
import SelectFE from "../../../../common/fieldEditors/SelectFE";
import { SubmitHandlerPlus } from "../../../../common/Form/types";

interface Props {
  parentId: string;
  open: boolean;
  tree: VariantTree;
  onClose: () => void;
}

function CreateVariantDialog(props: Props) {
  const { parentId, open, tree, onClose } = props;
  const [t] = useTranslation();
  const navigate = useNavigate();
  const [sourceList, setSourceList] = useState<Array<GenericInfo>>([]);
  const defaultValues = { name: "", sourceId: parentId };

  useEffect(() => {
    setSourceList(createListFromTree(tree));
  }, [tree]);

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleSubmit = (data: SubmitHandlerPlus<typeof defaultValues>) => {
    const { sourceId, name } = data.values;
    return createVariant(sourceId, name);
  };

  const handleSubmitSuccessful = async (
    data: SubmitHandlerPlus<typeof defaultValues>,
    variantId: string
  ) => {
    onClose();
    navigate(`/studies/${variantId}`);
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
      onSubmitSuccessful={handleSubmitSuccessful}
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

export default CreateVariantDialog;
