import { Box, Button, Drawer, RadioGroup } from "@mui/material";
import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import BooleanFE from "../../../../../common/fieldEditors/BooleanFE";
import NumberFE from "../../../../../common/fieldEditors/NumberFE";
import RadioFE from "../../../../../common/fieldEditors/RadioFE";
import Fieldset from "../../../../../common/Fieldset";
import { DataType, MAX_YEAR, Timestep } from "./utils";

export interface SelectionDrawerProps {
  open: boolean;
  onClose: () => void;
  values: {
    dataType: DataType;
    timestep: Timestep;
    year: number;
  };
  maxYear?: number;
  onSelection: (values: SelectionDrawerProps["values"]) => void;
}

function SelectionDrawer(props: SelectionDrawerProps) {
  const { open, onClose, values, maxYear = MAX_YEAR, onSelection } = props;
  const [dataTypeTmp, setDataTypeTmp] = useState(values.dataType);
  const [timestepTmp, setTimestepTemp] = useState(values.timestep);
  const [yearTmp, setYearTmp] = useState(values.year);
  const { t } = useTranslation();

  useEffect(() => {
    setDataTypeTmp(values.dataType);
    setTimestepTemp(values.timestep);
    setYearTmp(values.year);
  }, [values.dataType, values.timestep, values.year]);

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleSelection = () => {
    onSelection({
      dataType: dataTypeTmp,
      timestep: timestepTmp,
      year: yearTmp,
    });
    onClose();
  };

  const handleClose = () => {
    setDataTypeTmp(values.dataType);
    setTimestepTemp(values.timestep);
    setYearTmp(values.year);
    onClose();
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <Drawer
      open={open}
      onClose={handleClose}
      anchor="right"
      PaperProps={{ sx: { display: "flex" } }}
    >
      <Box sx={{ flex: 1, p: 3, overflow: "auto" }}>
        <Fieldset
          legend={t("study.results.mc")}
          contentProps={{ sx: { flexDirection: "column" } }}
        >
          <BooleanFE
            value={yearTmp <= 0}
            trueText="Synthesis"
            falseText="Year by year"
            onChange={(event) => {
              setYearTmp(event?.target.value ? -1 : 1);
            }}
          />
          {yearTmp > 0 && (
            <NumberFE
              sx={{ m: 0 }}
              label="Year"
              value={yearTmp}
              onChange={(event) => {
                const value = Number(event.target.value);
                setYearTmp(value > maxYear ? maxYear : value);
              }}
            />
          )}
        </Fieldset>
        <Fieldset legend={t("study.results.display")}>
          <RadioGroup
            value={dataTypeTmp}
            onChange={(_, value) => setDataTypeTmp(value as DataType)}
          >
            <RadioFE value={DataType.General} label="General values" />
            <RadioFE value={DataType.Thermal} label="Thermal plants" />
            <RadioFE value={DataType.Renewable} label="Ren. clusters" />
            <RadioFE value={DataType.Record} label="RecordYears" />
          </RadioGroup>
        </Fieldset>
        <Fieldset legend={t("study.results.temporality")}>
          <RadioGroup
            value={timestepTmp}
            onChange={(_, value) => setTimestepTemp(value as Timestep)}
          >
            <RadioFE value={Timestep.Hourly} label="Hourly" />
            <RadioFE value={Timestep.Daily} label="Daily" />
            <RadioFE value={Timestep.Weekly} label="Weekly" />
            <RadioFE value={Timestep.Monthly} label="Monthly" />
            <RadioFE value={Timestep.Annual} label="Annual" />
          </RadioGroup>
        </Fieldset>
      </Box>
      <Box sx={{ display: "flex", justifyContent: "flex-end", gap: 2, p: 2 }}>
        <Button variant="contained" onClick={handleSelection}>
          {t("global.apply")}
        </Button>
      </Box>
    </Drawer>
  );
}

export default SelectionDrawer;
