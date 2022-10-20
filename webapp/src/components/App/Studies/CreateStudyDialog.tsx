import debug from "debug";
import { useSnackbar } from "notistack";
import { useTranslation } from "react-i18next";
import { AxiosError } from "axios";
import { usePromise } from "react-use";
import * as R from "ramda";
import { StudyPublicMode } from "../../../common/types";
import useEnqueueErrorSnackbar from "../../../hooks/useEnqueueErrorSnackbar";
import { createStudy } from "../../../redux/ducks/studies";
import { getStudyVersionsFormatted, getGroups } from "../../../redux/selectors";
import useAppSelector from "../../../redux/hooks/useAppSelector";
import useAppDispatch from "../../../redux/hooks/useAppDispatch";
import FormDialog from "../../common/dialogs/FormDialog";
import StringFE from "../../common/fieldEditors/StringFE";
import SelectFE from "../../common/fieldEditors/SelectFE";
import Fieldset from "../../common/Fieldset";
import CheckboxesTagsFE from "../../common/fieldEditors/CheckboxesTagsFE";
import { SubmitHandlerPlus } from "../../common/Form";
import { PUBLIC_MODE_LIST } from "../../common/utils/constants";

const logErr = debug("antares:createstudyform:error");

interface FieldValues {
  name: string;
  version: string;
  publicMode: StudyPublicMode;
  groups: string[];
  tags: string[];
}

interface Props {
  open: boolean;
  onClose: VoidFunction;
}

function CreateStudyDialog(props: Props) {
  const [t] = useTranslation();
  const { open, onClose } = props;
  const { enqueueSnackbar } = useSnackbar();
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();
  const versionList = useAppSelector(getStudyVersionsFormatted);
  const groupList = useAppSelector(getGroups);
  const mounted = usePromise();
  const dispatch = useAppDispatch();

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleSubmit = async (data: SubmitHandlerPlus<FieldValues>) => {
    const { name, ...rest } = data.values;

    if (name && name.replace(/\s+/g, "") !== "") {
      try {
        await mounted(
          dispatch(
            createStudy({
              name,
              ...rest,
            })
          ).unwrap()
        );

        enqueueSnackbar(t("studies.success.createStudy", { studyname: name }), {
          variant: "success",
        });
      } catch (e) {
        logErr("Failed to create new study", name, e);
        enqueueErrorSnackbar(
          t("studies.error.createStudy", { studyname: name }),
          e as AxiosError
        );
      }
      onClose();
    } else {
      enqueueSnackbar(t("global.error.emptyName"), { variant: "error" });
    }
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <FormDialog
      title={t("studies.createNewStudy")}
      open={open}
      onCancel={onClose}
      onSubmit={handleSubmit}
      config={{
        defaultValues: {
          name: "",
          version: R.last(versionList)?.id.toString(),
          publicMode: "NONE",
          groups: [],
          tags: [],
        },
      }}
    >
      {({ control }) => (
        <>
          <StringFE
            label={t("studies.studyName")}
            name="name"
            control={control}
            rules={{ required: true }}
            sx={{ mx: 0 }}
            fullWidth
          />

          <SelectFE
            label={t("global.version")}
            options={versionList.map((ver) => ({
              label: ver.name,
              value: ver.id,
            }))}
            name="version"
            control={control}
            sx={{ mt: 1, mb: 5 }}
            fullWidth
          />

          <Fieldset legend={t("global.permission")} fullFieldWidth>
            <SelectFE
              label={t("study.publicMode")}
              options={PUBLIC_MODE_LIST.map((mode) => ({
                label: t(mode.name),
                value: mode.id,
              }))}
              name="publicMode"
              control={control}
              fullWidth
            />

            <SelectFE
              label={t("global.group")}
              options={groupList.map((group) => group.name)}
              name="groups"
              control={control}
              multiple
              fullWidth
            />
          </Fieldset>

          <Fieldset legend="Metadata" fullFieldWidth>
            <CheckboxesTagsFE
              options={[]}
              label={t("studies.enterTag")}
              freeSolo
              fullWidth
              sx={{ px: 0 }}
              name="tags"
              control={control}
            />
          </Fieldset>
        </>
      )}
    </FormDialog>
  );
}

export default CreateStudyDialog;
