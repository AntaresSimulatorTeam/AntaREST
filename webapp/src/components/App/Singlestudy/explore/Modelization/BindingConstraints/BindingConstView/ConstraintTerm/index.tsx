import { useMemo, useState } from "react";
import { Box, Button, TextField, Typography } from "@mui/material";
import AddCircleOutlineRoundedIcon from "@mui/icons-material/AddCircleOutlineRounded";
import DeleteRoundedIcon from "@mui/icons-material/DeleteRounded";
import { useTranslation } from "react-i18next";
import _ from "lodash";
import { ConstraintType, isDataLink } from "../utils";
import {
  AllClustersAndLinks,
  ClusterElement,
  LinkCreationInfoDTO,
} from "../../../../../../../../common/types";
import OptionsList from "./OptionsList";
import { ConstraintItemRoot } from "./style";
import { ConstraintElement } from "../constraintviews/ConstraintElement";
import { OffsetInput } from "../constraintviews/OffsetInput";

export const DEBOUNCE_DELAY = 250;
export type ConstraintWithNullableOffset = Partial<
  Omit<ConstraintType, "offset"> & { offset: number | null | undefined }
>;

interface ItemProps {
  options: AllClustersAndLinks;
  constraint: ConstraintType;
  constraintsTerm: Array<ConstraintType>;
  saveValue: (constraint: ConstraintWithNullableOffset) => void;
  deleteTerm: () => void;
}

export function ConstraintItem(props: ItemProps) {
  const { options, constraint, constraintsTerm, saveValue, deleteTerm } = props;
  const [t] = useTranslation();
  const [weight, setWeight] = useState(constraint.weight);
  const [offset, setOffset] = useState(constraint.offset);
  const isLink = useMemo(() => isDataLink(constraint.data), [constraint.data]);
  const initValue1 = useMemo(
    () =>
      isLink
        ? (constraint.data as LinkCreationInfoDTO).area1
        : (constraint.data as ClusterElement).area,
    [constraint.data, isLink]
  );
  const initValue2 = useMemo(
    () =>
      isLink
        ? (constraint.data as LinkCreationInfoDTO).area2
        : (constraint.data as ClusterElement).cluster,
    [constraint.data, isLink]
  );
  const [value1, setValue1] = useState(initValue1);
  const [value2, setValue2] = useState(initValue2);

  const handleOffset = _.debounce((value: string | number | null) => {
    let pValue;
    if (value !== null) {
      try {
        pValue = typeof value === "number" ? value : parseFloat(value);
        pValue = Number.isNaN(pValue) ? 0 : pValue;
      } catch (e) {
        pValue = 0;
      }
    }
    setOffset(pValue);
    saveValue({
      id: constraint.id,
      offset: value === null ? value : pValue,
    });
  }, DEBOUNCE_DELAY);

  const handleWeight = _.debounce((value: string | number) => {
    let pValue = 0;
    try {
      pValue = typeof value === "number" ? value : parseFloat(value);
      pValue = Number.isNaN(pValue) ? 0 : pValue;
    } catch (e) {
      pValue = 0;
    }
    setWeight(pValue);
    saveValue({
      id: constraint.id,
      weight: pValue,
    });
  }, DEBOUNCE_DELAY);

  return (
    <ConstraintItemRoot>
      <ConstraintElement
        title="Weight"
        left={
          <TextField
            label={t("study.modelization.bindingConst.weight")}
            variant="filled"
            type="number"
            value={weight}
            onChange={(e) => handleWeight(e.target.value)}
          />
        }
        right={
          <Box sx={{ display: "flex", alignItems: "center" }}>
            <OptionsList
              isLink={isLink}
              list={options}
              constraint={constraint}
              saveValue={saveValue}
              value1={value1}
              value2={value2}
              setValue1={setValue1}
              setValue2={setValue2}
              constraintsTerm={constraintsTerm}
            />
          </Box>
        }
      />
      {offset !== undefined && offset !== null ? (
        <>
          <Typography sx={{ mx: 1 }}>x</Typography>
          <ConstraintElement
            title="Offset"
            operator="+"
            left={<Typography>t</Typography>}
            right={
              <OffsetInput onRemove={() => handleOffset(null)}>
                <TextField
                  label={t("study.modelization.bindingConst.offset")}
                  variant="filled"
                  type="number"
                  value={offset}
                  onChange={(e) => handleOffset(e.target.value)}
                />
              </OffsetInput>
            }
          />
        </>
      ) : (
        <Button
          variant="text"
          color="secondary"
          startIcon={<AddCircleOutlineRoundedIcon />}
          sx={{ ml: 1 }}
          onClick={() => handleOffset(0)}
        >
          {t("study.modelization.bindingConst.offset")}
        </Button>
      )}
      <Button
        variant="text"
        color="error"
        sx={{ mx: 1 }}
        startIcon={<DeleteRoundedIcon />}
        onClick={deleteTerm}
      >
        {t("global.delete")}
      </Button>
    </ConstraintItemRoot>
  );
}
