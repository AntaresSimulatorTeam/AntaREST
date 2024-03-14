import { useCallback, useMemo, useState } from "react";
import { Box, Button, TextField, Typography } from "@mui/material";
import AddCircleOutlineRoundedIcon from "@mui/icons-material/AddCircleOutlineRounded";
import DeleteRoundedIcon from "@mui/icons-material/DeleteRounded";
import { useTranslation } from "react-i18next";
import { ConstraintTerm, isDataLink } from "../utils";
import {
  AllClustersAndLinks,
  ClusterElement,
  LinkCreationInfoDTO,
} from "../../../../../../../../common/types";
import OptionsList from "./OptionsList";
import ConstraintElement from "../constraintviews/ConstraintElement";
import OffsetInput from "../constraintviews/OffsetInput";

export type ConstraintWithNullableOffset = Partial<
  Omit<ConstraintTerm, "offset"> & { offset: number | null | undefined }
>;

interface Props {
  options: AllClustersAndLinks;
  term: ConstraintTerm;
  constraintTerms: ConstraintTerm[];
  saveValue: (term: ConstraintWithNullableOffset) => void;
  deleteTerm: () => void;
}

function ConstraintTermItem(props: Props) {
  const { options, term, constraintTerms, saveValue, deleteTerm } = props;
  const [t] = useTranslation();
  const [weight, setWeight] = useState(term.weight);
  const [offset, setOffset] = useState(term.offset);
  const isLink = useMemo(() => isDataLink(term.data), [term.data]);
  const initValue1 = isLink
    ? (term.data as LinkCreationInfoDTO).area1
    : (term.data as ClusterElement).area;
  const initValue2 = isLink
    ? (term.data as LinkCreationInfoDTO).area2
    : (term.data as ClusterElement).cluster;
  const [value1, setValue1] = useState(initValue1);
  const [value2, setValue2] = useState(initValue2);

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleChange = useCallback(
    (name: "weight" | "offset", value: string | number | null) => {
      let pValue = 0;
      if (value !== null) {
        try {
          pValue = typeof value === "number" ? value : parseFloat(value);
          pValue = Number.isNaN(pValue) ? 0 : pValue;
        } catch (e) {
          pValue = 0;
        }
      }
      if (name === "weight") {
        setWeight(pValue);
      } else {
        setOffset(pValue);
      }
      saveValue({
        id: term.id,
        [name]: value === null ? value : pValue,
      });
    },
    [term.id, saveValue],
  );

  ////////////////////////////////////////////////////////////////
  // JSX
  /// /////////////////////////////////////////////////////////////

  return (
    <Box
      sx={{
        display: "flex",
        width: "100%",
        padding: 0,
        alignItems: "center",
      }}
    >
      <ConstraintElement
        title="Weight"
        left={
          <TextField
            label={t("study.modelization.bindingConst.weight")}
            variant="filled"
            type="number"
            value={weight}
            onChange={(e) => handleChange("weight", e.target.value)}
          />
        }
        right={
          <Box sx={{ display: "flex", alignItems: "center" }}>
            <OptionsList
              isLink={isLink}
              list={options}
              term={term}
              saveValue={saveValue}
              value1={value1}
              value2={value2}
              setValue1={setValue1}
              setValue2={setValue2}
              constraintTerms={constraintTerms}
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
              <OffsetInput onRemove={() => handleChange("offset", null)}>
                <TextField
                  label={t("study.modelization.bindingConst.offset")}
                  variant="filled"
                  type="number"
                  value={offset}
                  onChange={(e) => handleChange("offset", e.target.value)}
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
          onClick={() => handleChange("offset", 0)}
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
    </Box>
  );
}

export default ConstraintTermItem;
