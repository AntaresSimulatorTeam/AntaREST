import { useMemo, useState } from "react";
import { Box, Button, TextField, Typography } from "@mui/material";
import AddCircleOutlineRoundedIcon from "@mui/icons-material/AddCircleOutlineRounded";
import DeleteRoundedIcon from "@mui/icons-material/DeleteRounded";
import { useTranslation } from "react-i18next";
import { ConstraintTerm, isLinkTerm } from "../utils";
import { AllClustersAndLinks } from "../../../../../../../../common/types";
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

function ConstraintTermItem({
  options,
  term,
  constraintTerms,
  saveValue,
  deleteTerm,
}: Props) {
  const [t] = useTranslation();
  const [weight, setWeight] = useState(term.weight);
  const [offset, setOffset] = useState(term.offset);
  const isLink = useMemo(() => isLinkTerm(term.data), [term.data]);

  const [value1, value2] = useMemo(() => {
    if (isLinkTerm(term.data)) {
      const { area1, area2 } = term.data;
      return [area1, area2];
    } else {
      const { area, cluster } = term.data;
      return [area, cluster];
    }
  }, [term.data]);

  const [selectedValue1, setSelectedValue1] = useState(value1);
  const [selectedValue2, setSelectedValue2] = useState(value2);

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleChange = (
    name: "weight" | "offset",
    value: string | number | null,
  ) => {
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
  };

  ////////////////////////////////////////////////////////////////
  // Utils
  ////////////////////////////////////////////////////////////////

  return (
    <Box
      sx={{
        display: "flex",
        alignItems: "center",
      }}
    >
      <ConstraintElement
        left={
          <TextField
            label={t("study.modelization.bindingConst.weight")}
            variant="outlined"
            size="small"
            type="number"
            value={weight}
            onChange={(e) => handleChange("weight", e.target.value)}
            sx={{ maxWidth: 150, mx: 0 }}
          />
        }
        right={
          <Box sx={{ display: "flex", alignItems: "center" }}>
            <OptionsList
              isLink={isLink}
              list={options}
              term={term}
              saveValue={saveValue}
              value1={selectedValue1}
              value2={selectedValue2}
              setValue1={setSelectedValue1}
              setValue2={setSelectedValue2}
              constraintTerms={constraintTerms}
            />
          </Box>
        }
      />

      <Box sx={{ display: "flex", alignItems: "center" }}>
        {offset !== undefined && offset !== null ? (
          <>
            <Typography sx={{ mx: 1 }}>x</Typography>
            <ConstraintElement
              operator="+"
              left={<Typography>t</Typography>}
              right={
                <OffsetInput onRemove={() => handleChange("offset", null)}>
                  <TextField
                    label={t("study.modelization.bindingConst.offset")}
                    variant="outlined"
                    size="small"
                    type="number"
                    value={offset}
                    onChange={(e) => handleChange("offset", e.target.value)}
                    sx={{ maxWidth: 100 }}
                  />
                </OffsetInput>
              }
            />
          </>
        ) : (
          <Button
            variant="outlined"
            color="secondary"
            size="small"
            startIcon={<AddCircleOutlineRoundedIcon />}
            onClick={() => handleChange("offset", 0)}
            sx={{ ml: 3.5 }}
          >
            {t("study.modelization.bindingConst.offset")}
          </Button>
        )}
      </Box>

      <Box sx={{ display: "flex", alignItems: "center", ml: "auto" }}>
        <Button
          variant="outlined"
          color="error"
          size="small"
          startIcon={<DeleteRoundedIcon />}
          onClick={deleteTerm}
        >
          {t("global.delete")}
        </Button>
      </Box>
    </Box>
  );
}

export default ConstraintTermItem;
