import UpgradeIcon from "@mui/icons-material/Upgrade";
import { useMemo } from "react";
import { useTranslation } from "react-i18next";
import { StudyMetadata } from "../../../common/types";
import { SubmitHandlerPlus } from "../../common/Form/types";
import Fieldset from "../../common/Fieldset";
import SelectFE from "../../common/fieldEditors/SelectFE";
import FormDialog from "../../common/dialogs/FormDialog";
import useAppSelector from "../../../redux/hooks/useAppSelector";
import { getStudyVersionsFormatted } from "../../../redux/selectors";
import { upgradeStudy } from "../../../services/api/study";

interface Props {
  study: StudyMetadata;
  onClose: () => void;
  open: boolean;
}

const defaultValues = {
  version: "",
};

function UpgradeDialog({ study, onClose, open }: Props) {
  const [t] = useTranslation();
  const versions = useAppSelector(getStudyVersionsFormatted);
  const versionOptions = useMemo(() => {
    return versions
      .filter((version) => version.id > study.version)
      .sort((a, b) => b.name.localeCompare(a.name))
      .map(({ id, name }) => ({
        value: id,
        label: name,
      }));
  }, [versions, study.version]);

  ////////////////////////////////////////////////////////////////
  // Event handlers
  ////////////////////////////////////////////////////////////////

  const handleSubmit = async (
    data: SubmitHandlerPlus<typeof defaultValues>
  ) => {
    return upgradeStudy(study.id, data.values.version).then(onClose);
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <FormDialog
      title={t("study.upgrade")}
      titleIcon={UpgradeIcon}
      submitButtonText={t("study.upgrade")}
      open={open}
      onCancel={onClose}
      onSubmit={handleSubmit}
      config={{ defaultValues }}
    >
      {({ control }) => (
        <Fieldset fullFieldWidth>
          <SelectFE
            name="version"
            label="Version"
            variant="filled"
            options={versionOptions}
            control={control}
          />
        </Fieldset>
      )}
    </FormDialog>
  );
}

export default UpgradeDialog;
