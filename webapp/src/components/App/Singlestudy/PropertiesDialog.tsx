import debug from "debug";
import * as R from "ramda";
import { useTranslation } from "react-i18next";
import { AxiosError } from "axios";
import { useSnackbar } from "notistack";
import { useMemo } from "react";
import { StudyMetadata } from "../../../common/types";
import {
  addStudyGroup,
  changePublicMode,
  deleteStudyGroup,
  updateStudyMetadata,
} from "../../../services/api/study";
import { getGroups } from "../../../services/api/user";
import useEnqueueErrorSnackbar from "../../../hooks/useEnqueueErrorSnackbar";
import { PUBLIC_MODE_LIST } from "../../common/utils/constants";
import usePromiseWithSnackbarError from "../../../hooks/usePromiseWithSnackbarError";
import FormDialog from "../../common/dialogs/FormDialog";
import StringFE from "../../common/fieldEditors/StringFE";
import SelectFE from "../../common/fieldEditors/SelectFE";
import CheckboxesTagsFE from "../../common/fieldEditors/CheckboxesTagsFE";
import Fieldset from "../../common/Fieldset";
import { SubmitHandlerPlus } from "../../common/Form/types";
import useAppDispatch from "../../../redux/hooks/useAppDispatch";
import { updateStudy } from "../../../redux/ducks/studies";

const logErr = debug("antares:createstudyform:error");

interface Props {
  open: boolean;
  onClose: () => void;
  study: StudyMetadata;
  updateStudyData?: VoidFunction;
}

function PropertiesDialog(props: Props) {
  const [t] = useTranslation();
  const { open, onClose, study, updateStudyData } = props;
  const { enqueueSnackbar } = useSnackbar();
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();
  const dispatch = useAppDispatch();

  const { data: groupList = [] } = usePromiseWithSnackbarError(getGroups, {
    errorMessage: t("settings.error.groupsError"),
  });

  const defaultValues = useMemo(
    () => ({
      name: study.name,
      publicMode: study.publicMode,
      groups: study.groups.map((group) => group.id),
      tags: study.tags ? study.tags : [],
    }),
    [study]
  );

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleSubmit = async (
    data: SubmitHandlerPlus<typeof defaultValues>
  ) => {
    const { name, tags, groups, publicMode } = data.dirtyValues;
    const { id: studyId } = study;

    try {
      // TODO create redux thunk

      // Update metadata
      if (name || tags) {
        await updateStudyMetadata(studyId, {
          name: data.values.name,
          tags: data.values.tags,
        });
      }

      // Update public mode
      if (publicMode) {
        await changePublicMode(studyId, publicMode);
      }

      // Update group
      if (groups) {
        const toDelete = R.difference(defaultValues.groups, groups);
        const toAdd = R.difference(groups, defaultValues.groups);

        await Promise.all(
          toDelete.map((id) => deleteStudyGroup(studyId, id as string))
        );

        await Promise.all(
          toAdd.map((id) => addStudyGroup(studyId, id as string))
        );
      }

      if (updateStudyData) {
        updateStudyData();
      } else {
        dispatch(
          updateStudy({
            id: study.id,
            changes: {
              name: data.values.name,
              tags: data.values.tags,
            },
          })
        );
      }

      enqueueSnackbar(t("studies.success.saveData"), {
        variant: "success",
      });
    } catch (e) {
      logErr("Failed to create new study", name, e);
      enqueueErrorSnackbar(t("studies.error.saveData"), e as AxiosError);
    }

    onClose();
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <FormDialog
      title={t("study.properties")}
      open={open}
      onCancel={onClose}
      onSubmit={handleSubmit}
      config={{ defaultValues }}
    >
      {({ control }) => (
        <>
          <StringFE
            label={t("studies.studyName")}
            name="name"
            control={control}
            rules={{ required: true, validate: (val) => val.trim().length > 0 }}
            sx={{ mx: 0 }}
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
              options={groupList.map((group) => ({
                label: group.name,
                value: group.id,
              }))}
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

export default PropertiesDialog;
