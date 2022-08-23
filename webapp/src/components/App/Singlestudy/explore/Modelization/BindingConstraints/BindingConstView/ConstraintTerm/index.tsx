import { ReactNode, useCallback, useMemo, useState } from "react";
import {
  Box,
  Button,
  FormControlLabel,
  Switch,
  TextField,
  Typography,
} from "@mui/material";
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
import {
  ConstraintElementData,
  ConstraintElementHeader,
  ConstraintElementRoot,
  ConstraintItemRoot,
} from "./style";

export const DEBOUNCE_DELAY = 250;

interface ElementProps {
  title: string;
  left: ReactNode;
  right: ReactNode;
  operator?: string;
  isLink?: boolean;
  onToggleType?: () => void;
}

export function ConstraintElement(props: ElementProps) {
  const { title, isLink, left, right, operator, onToggleType } = props;
  return (
    <ConstraintElementRoot>
      <ConstraintElementHeader>
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
      </ConstraintElementHeader>
      <ConstraintElementData>
        {left}
        <Typography sx={{ mx: 1 }}>{operator}</Typography>
        {right}
      </ConstraintElementData>
    </ConstraintElementRoot>
  );
}

ConstraintElement.defaultProps = {
  operator: "x",
};

interface ItemProps {
  options: AllClustersAndLinks;
  constraint: ConstraintType;
  saveValue: (constraint: Partial<ConstraintType>) => void;
  deleteTerm: () => void;
}

export function ConstraintItem(props: ItemProps) {
  const { options, constraint, saveValue, deleteTerm } = props;
  const [t] = useTranslation();
  const [isLink, setIsLink] = useState(isDataLink(constraint.data));
  const [weight, setWeight] = useState(constraint.weight);
  const [offset, setOffset] = useState(constraint.offset);
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

  const handleOffset = _.debounce((value: string | number) => {
    let pValue = 0;
    try {
      pValue = typeof value === "number" ? value : parseFloat(value);
      pValue = Number.isNaN(pValue) ? 0 : pValue;
    } catch (e) {
      pValue = 0;
    }
    setOffset(pValue);
    saveValue({
      id: constraint.id,
      offset: pValue,
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

  const handleToggleLink = useCallback((): void => {
    const v1 = isLink
      ? options.clusters[0].element.id
      : options.links[0].element.id;
    const v2 = isLink
      ? options.clusters[0].item_list[0].id
      : options.links[0].item_list[0].id;
    saveValue({
      id: constraint.id,
      data: isLink
        ? {
            area: v1,
            cluster: v2,
          }
        : {
            area1: v1,
            area2: v2,
          },
    });
    setValue1(v1);
    setValue2(v2);
    setIsLink((value) => !value);
  }, [constraint, isLink, options.clusters, options.links, saveValue]);

  return (
    <ConstraintItemRoot>
      <ConstraintElement
        title="Weight"
        isLink={isLink}
        onToggleType={handleToggleLink}
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
                label={t("study.modelization.bindingConst.offset")}
                variant="filled"
                type="number"
                value={offset}
                onChange={(e) => handleOffset(e.target.value)}
              />
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
