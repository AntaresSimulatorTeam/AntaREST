import {
  Box,
  Button,
  FormControlLabel,
  Paper,
  Switch,
  Typography,
} from "@mui/material";
import AddCircleOutlineRoundedIcon from "@mui/icons-material/AddCircleOutlineRounded";
import { ReactNode, useCallback, useState } from "react";
import { useTranslation } from "react-i18next";
import { AxiosError } from "axios";
import SelectFE from "../../../../../../../common/fieldEditors/SelectFE";
import TextSeparator from "../../../../../../../common/TextSeparator";
import { BindingConstFields, ConstraintType } from "../utils";
import { useFormContext } from "../../../../../../../common/Form";
import NumberFE from "../../../../../../../common/fieldEditors/NumberFE";
import useEnqueueErrorSnackbar from "../../../../../../../../hooks/useEnqueueErrorSnackbar";
import { LinkCreationInfoDTO } from "../../../../../../../../common/types";
import { updateConstraint } from "../../../../../../../../services/api/studydata";

interface ElementProps {
  title: string;
  left: ReactNode;
  right: ReactNode;
  operator?: string;
  isLink?: boolean;
  onToggleType?: () => void;
}
function ConstraintElement(props: ElementProps) {
  const { title, isLink, left, right, operator, onToggleType } = props;
  return (
    <Paper
      sx={{
        display: "flex",
        flexDirection: "column",
        p: 1,
      }}
    >
      <Box
        sx={{
          width: "100%",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
        }}
      >
        <Typography
          sx={{
            color: "grey.400",
            fontSize: "16px",
          }}
        >
          {title}
        </Typography>
        {onToggleType !== undefined && (
          <FormControlLabel
            control={<Switch checked={isLink === true} />}
            onChange={(event, checked) => onToggleType()}
            label={isLink ? "Link" : "Cluster"}
            labelPlacement="end"
          />
        )}
      </Box>
      <Box
        sx={{
          width: "100%",
          display: "flex",
          justifyContent: "center",
          alignItems: "center",
        }}
      >
        {left}
        <Typography sx={{ mx: 1 }}>{operator}</Typography>
        {right}
      </Box>
    </Paper>
  );
}

ConstraintElement.defaultProps = {
  operator: "x",
};

interface ItemProps {
  constraint: ConstraintType;
  options1: Array<string>;
  options2: Array<string>;
  saveValue: (constraint: ConstraintType) => void;
}

function ConstraintItem(props: ItemProps) {
  const { constraint, options1, options2, saveValue } = props;
  const { control } = useFormContext<BindingConstFields>();
  const [t] = useTranslation();
  const [isLink, setIsLink] = useState(
    (constraint.data as LinkCreationInfoDTO).area1 !== undefined
  );

  const handleToggleLink = (): void => {
    saveValue({
      ...constraint,
      data: isLink
        ? {
            area: "",
            cluster: "",
          }
        : {
            area1: "",
            area2: "",
          },
    });

    setIsLink((value) => !value);
  };

  return (
    <Box
      sx={{
        display: "flex",
        width: "100%",
        alignItems: "center",
      }}
    >
      <ConstraintElement
        title="Weight"
        isLink={isLink}
        onToggleType={handleToggleLink}
        left={
          <NumberFE
            name={constraint.id}
            label={t("global.value")}
            variant="filled"
            control={control}
            rules={{
              onAutoSubmit: (data) =>
                saveValue({ ...constraint, weight: data }),
              required: t("form.field.required") as string,
            }}
          />
        }
        right={
          <Box sx={{ display: "flex", width: "100%", alignItems: "center" }}>
            <SelectFE
              name={`constraints.${constraint.id}.data.${
                !isLink ? "area" : "area1"
              }`}
              label={t("study.modelization.configuration.general.year")}
              options={options1}
              control={control}
              rules={{
                onAutoSubmit: (value) =>
                  saveValue({
                    ...constraint,
                    data: !isLink
                      ? {
                          ...constraint.data,
                          area: value,
                        }
                      : {
                          ...constraint.data,
                          area1: value,
                        },
                  }),
                required: t("form.field.required") as string,
              }}
            />
            <SelectFE
              name={`constraints.${constraint.id}.data.${
                !isLink ? "cluster" : "area2"
              }`}
              label={t("study.modelization.configuration.general.year")}
              options={options2}
              control={control}
              rules={{
                onAutoSubmit: (value) =>
                  saveValue({
                    ...constraint,
                    data: !isLink
                      ? {
                          ...constraint.data,
                          cluster: value,
                        }
                      : {
                          ...constraint.data,
                          area2: value,
                        },
                  }),
                required: t("form.field.required") as string,
              }}
            />
          </Box>
        }
      />
      {constraint.offset !== undefined ? (
        <>
          <Typography sx={{ mx: 1 }}>X</Typography>
          <ConstraintElement
            title="Offset"
            operator="+"
            left={<Typography>t</Typography>}
            right={
              <NumberFE
                name={`constraints.${constraint.id}.offset`}
                label={t("global.value")}
                variant="filled"
                control={control}
                rules={{
                  onAutoSubmit: (data) =>
                    saveValue({ ...constraint, offset: data }),
                  required: t("form.field.required") as string,
                }}
              />
            }
          />
        </>
      ) : (
        <Button
          variant="text"
          color="secondary"
          startIcon={<AddCircleOutlineRoundedIcon />}
          onClick={() => saveValue({ ...constraint, offset: 0 })}
        >
          OFFSET
        </Button>
      )}
    </Box>
  );
}

interface Props {
  fieldset?: boolean;
  constraint: ConstraintType;
  bindingConst: string;
  studyId: string;
  // control: ControlPlus<BindingConstFields, any>;
  // defaultValues: Partial<BindingConstFields>;
}
export default function Constraint(props: Props) {
  const { bindingConst, studyId, fieldset, constraint } = props;
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();
  const [t] = useTranslation();

  const saveValue = useCallback(
    async (constraint: ConstraintType) => {
      try {
        await updateConstraint(studyId, bindingConst, constraint);
        // console.log("Constraint: ", constraint);
      } catch (error) {
        enqueueErrorSnackbar(t("study.error.updateUI"), error as AxiosError);
      }
    },
    [bindingConst, enqueueErrorSnackbar, studyId, t]
  );

  return fieldset === true ? (
    <Box
      sx={{
        display: "flex",
        width: "100%",
        flexDirection: "column",
      }}
    >
      <TextSeparator
        text="+"
        rootStyle={{ my: 0.25 }}
        textStyle={{ fontSize: "22px" }}
      />
      <ConstraintItem
        constraint={constraint}
        options1={[]}
        options2={[]}
        saveValue={saveValue}
      />
    </Box>
  ) : (
    <ConstraintItem
      constraint={constraint}
      options1={[]}
      options2={[]}
      saveValue={saveValue}
    />
  );
}

Constraint.defaultProps = {
  fieldset: undefined,
};
