import {
  Backdrop,
  Box,
  Button,
  CircularProgress,
  FormControlLabel,
  Switch,
  TextField,
  Typography,
} from "@mui/material";
import { useSnackbar } from "notistack";
import { useState } from "react";
import { Controller, FieldValues, useForm } from "react-hook-form";
import { useTranslation } from "react-i18next";
import { useUpdateEffect } from "react-use";
import useEnqueueErrorSnackbar from "../../../hooks/useEnqueueErrorSnackbar";
import usePromiseWithSnackbarError from "../../../hooks/usePromiseWithSnackbarError";
import {
  getMaintenanceMode,
  getMessageInfo,
  updateMaintenanceMode,
  updateMessageInfo,
} from "../../../services/api/maintenance";
import ConfirmationDialog from "../../common/dialogs/ConfirmationDialog";

function Maintenance() {
  const { t } = useTranslation();
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();
  const { enqueueSnackbar } = useSnackbar();
  const [showConfirmationModal, setShowConfirmationModal] = useState(false);

  const {
    register,
    setValue,
    control,
    handleSubmit,
    reset,
    formState: { isDirty, isSubmitting },
  } = useForm();

  const {
    data: initialValues,
    isLoading,
    error,
    reload: reloadFetchMaintenance,
  } = usePromiseWithSnackbarError(
    async () => ({
      mode: await getMaintenanceMode(),
      message: await getMessageInfo(),
    }),
    t("settings:maintenanceError")
  );

  useUpdateEffect(() => {
    if (initialValues) {
      reset();
      setValue("mode", initialValues.mode);
      setValue("message", initialValues.message);
    }
  }, [initialValues]);

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleSave = handleSubmit(async (data: FieldValues) => {
    setShowConfirmationModal(false);

    try {
      if (initialValues?.mode !== data.mode) {
        await updateMaintenanceMode(data.mode);
      }

      if (initialValues?.message !== data.message) {
        await updateMessageInfo(data.message);
      }

      enqueueSnackbar(t("settings:onUpdateMaintenance"), {
        variant: "success",
      });
    } catch (e) {
      enqueueErrorSnackbar(t("settings:onUpdateMaintenanceError"), e as Error);
    } finally {
      reloadFetchMaintenance();
    }
  });

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  if (error) {
    return (
      <Typography sx={{ m: 2 }} align="center">
        {t("settings:maintenanceError")}
      </Typography>
    );
  }

  return (
    <>
      <Box
        sx={{ display: "flex", flexDirection: "column", position: "relative" }}
      >
        <Box>
          <FormControlLabel
            sx={{ mb: 1 }}
            control={
              <Controller
                control={control}
                name="mode"
                defaultValue={false}
                render={({ field: { value, ref, ...rest } }) => (
                  <Switch checked={value} inputRef={ref} {...rest} />
                )}
              />
            }
            label={t("settings:maintenanceMode")}
            labelPlacement="start"
          />
        </Box>
        <TextField
          label={t("settings:messageMode")}
          InputLabelProps={{ shrink: true }}
          minRows={6}
          multiline
          {...register("message")}
        />
        <Button
          disabled={!isDirty}
          onClick={() => setShowConfirmationModal(true)}
        >
          {t("main:save")}
        </Button>
        <Backdrop
          open={isLoading || isSubmitting}
          sx={{
            position: "absolute",
            zIndex: (theme) => theme.zIndex.drawer + 1,
          }}
        >
          <CircularProgress color="inherit" />
        </Backdrop>
      </Box>
      {showConfirmationModal && (
        <ConfirmationDialog
          onCancel={() => setShowConfirmationModal(false)}
          onConfirm={handleSave}
          alert="warning"
          open
        >
          {t("settings:updateMaintenanceConfirmation")}
        </ConfirmationDialog>
      )}
    </>
  );
}

export default Maintenance;
