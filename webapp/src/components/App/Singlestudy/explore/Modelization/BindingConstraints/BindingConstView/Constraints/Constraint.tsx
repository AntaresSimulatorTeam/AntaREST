import { ReactNode, useCallback, useState } from "react";
import {
  Box,
  Button,
  FormControlLabel,
  Paper,
  Switch,
  Typography,
} from "@mui/material";
import AddCircleOutlineRoundedIcon from "@mui/icons-material/AddCircleOutlineRounded";
import { useTranslation } from "react-i18next";
import { AxiosError } from "axios";
import TextSeparator from "../../../../../../../common/TextSeparator";
import { BindingConstFields, ConstraintType } from "../utils";
import useEnqueueErrorSnackbar from "../../../../../../../../hooks/useEnqueueErrorSnackbar";
import {
  AllClustersAndLinks,
  LinkCreationInfoDTO,
} from "../../../../../../../../common/types";
import { updateConstraintTerm } from "../../../../../../../../services/api/studydata";
import OptionsList from "./OptionsList";
import NumberFE from "../../../../../../../common/fieldEditors/NumberFE";
import { ControlPlus } from "../../../../../../../common/Form";

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
  options: AllClustersAndLinks;
  index: number;
  constraint: ConstraintType;
  control: ControlPlus<BindingConstFields, any>;
  saveValue: (constraint: ConstraintType) => void;
}

function ConstraintItem(props: ItemProps) {
  const { options, control, constraint, index, saveValue } = props;
  const [t] = useTranslation();
  const [isLink, setIsLink] = useState(
    (constraint.data as LinkCreationInfoDTO).area1 !== undefined
  );
  console.log("OPTIONS: ", options);

  const handleToggleLink = useCallback((): void => {
    console.log("TOGGLE: ", !isLink);
    saveValue({
      ...constraint,
      data: isLink
        ? {
            area: options.clusters[0].element.id,
            cluster: options.clusters[0].item_list[0].id,
          }
        : {
            area1: options.links[0].element.id,
            area2: options.links[0].item_list[0].id,
          },
    });

    setIsLink((value) => !value);
  }, [constraint, isLink, options.clusters, options.links, saveValue]);

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
            name={`constraints.${index}.weight`}
            label={t("global.value")}
            variant="filled"
            control={control}
            rules={{
              onAutoSubmit: (value) =>
                saveValue({
                  ...constraint,
                  weight: parseFloat(value),
                }),
            }}
          />
        }
        right={
          <Box sx={{ display: "flex", alignItems: "center" }}>
            <OptionsList
              isLink={isLink}
              list={options}
              constraint={constraint}
              control={control}
              index={index}
              saveValue={saveValue}
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
              <NumberFE
                name={`constraints.${index}.offset`}
                label={t("global.value")}
                variant="filled"
                control={control}
                rules={{
                  onAutoSubmit: (value) =>
                    saveValue({
                      ...constraint,
                      offset: parseFloat(value),
                    }),
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
  index: number;
  bindingConst: string;
  studyId: string;
  constraint: ConstraintType;
  options: AllClustersAndLinks;
  control: ControlPlus<BindingConstFields, any>;
}
export default function Constraint(props: Props) {
  const { bindingConst, control, constraint, options, studyId, index } = props;
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();
  const [t] = useTranslation();

  console.log("HELLO: ", index);

  const saveValue = useCallback(
    async (constraint: ConstraintType) => {
      try {
        console.log("UPDATE ", index, " with ", constraint);
        await updateConstraintTerm(studyId, bindingConst, constraint);
        // console.log("Constraint: ", constraint);
      } catch (error) {
        enqueueErrorSnackbar(t("study.error.updateUI"), error as AxiosError);
      }
    },
    [bindingConst, enqueueErrorSnackbar, index, studyId, t]
  );

  return index > 0 ? (
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
        options={options}
        saveValue={saveValue}
        constraint={constraint}
        index={index}
        control={control}
      />
    </Box>
  ) : (
    <ConstraintItem
      options={options}
      saveValue={saveValue}
      constraint={constraint}
      index={index}
      control={control}
    />
  );
}
