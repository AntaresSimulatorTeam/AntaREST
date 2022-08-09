import {
  Box,
  Button,
  FormControlLabel,
  Paper,
  Switch,
  TextField,
  Typography,
} from "@mui/material";
import AddCircleOutlineRoundedIcon from "@mui/icons-material/AddCircleOutlineRounded";
import { ReactNode, useCallback, useState } from "react";
import { useTranslation } from "react-i18next";
import { AxiosError } from "axios";
import TextSeparator from "../../../../../../../common/TextSeparator";
import { ConstraintType } from "../utils";
import useEnqueueErrorSnackbar from "../../../../../../../../hooks/useEnqueueErrorSnackbar";
import {
  AllClustersAndLinks,
  ClusterElement,
  LinkCreationInfoDTO,
} from "../../../../../../../../common/types";
import { updateConstraintTerm } from "../../../../../../../../services/api/studydata";
import OptionsList from "./OptionsList";

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
  options: AllClustersAndLinks;
  saveValue: (constraint: ConstraintType) => void;
}

function ConstraintItem(props: ItemProps) {
  const { constraint, options, saveValue } = props;
  const [t] = useTranslation();
  const { weight, offset, data } = constraint;
  const [isLink, setIsLink] = useState(
    (data as LinkCreationInfoDTO).area1 !== undefined
  );
  console.log("OPTIONS: ", options);
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
          <TextField
            type="number"
            variant="filled"
            label={t("global.value")}
            value={weight}
            onChange={(e) =>
              saveValue({
                ...constraint,
                weight: parseFloat(e.target.value),
              })
            }
          />
        }
        right={
          <Box sx={{ display: "flex", alignItems: "center" }}>
            <OptionsList
              options={isLink ? options.links : options.clusters}
              label1={t(isLink ? "study.area1" : "study.area")}
              label2={t(isLink ? "study.area2" : "study.cluster")}
              value1={
                isLink
                  ? (constraint.data as LinkCreationInfoDTO).area1
                  : (constraint.data as ClusterElement).area
              }
              value2={
                isLink
                  ? (constraint.data as LinkCreationInfoDTO).area2
                  : (constraint.data as ClusterElement).cluster
              }
              onChangeOption={(option1, option2) =>
                saveValue({
                  ...constraint,
                  data: isLink
                    ? {
                        area1: option1,
                        area2: option2,
                      }
                    : {
                        area: option1,
                        cluster: option2,
                      },
                })
              }
            />
          </Box>
        }
      />
      {constraint.offset !== undefined && constraint.offset !== null ? (
        <>
          <Typography sx={{ mx: 1 }}>x</Typography>
          <ConstraintElement
            title="Offset"
            operator="+"
            left={<Typography>t</Typography>}
            right={
              <TextField
                type="number"
                variant="filled"
                label={t("global.value")}
                value={offset}
                onChange={(e) =>
                  saveValue({
                    ...constraint,
                    offset: parseFloat(e.target.value),
                  })
                }
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
  options: AllClustersAndLinks;
  onUpdate: () => void;
}
export default function Constraint(props: Props) {
  const { bindingConst, options, studyId, fieldset, constraint, onUpdate } =
    props;
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();
  const [t] = useTranslation();

  const saveValue = useCallback(
    async (constraint: ConstraintType) => {
      try {
        await updateConstraintTerm(studyId, bindingConst, constraint);
        onUpdate();
        // console.log("Constraint: ", constraint);
      } catch (error) {
        enqueueErrorSnackbar(t("study.error.updateUI"), error as AxiosError);
      }
    },
    [bindingConst, enqueueErrorSnackbar, onUpdate, studyId, t]
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
        options={options}
        saveValue={saveValue}
      />
    </Box>
  ) : (
    <ConstraintItem
      constraint={constraint}
      options={options}
      saveValue={saveValue}
    />
  );
}

Constraint.defaultProps = {
  fieldset: undefined,
};
