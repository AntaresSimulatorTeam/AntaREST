import * as R from "ramda";
import { Box, Button, Divider } from "@mui/material";
import { useEffect } from "react";
import { useTranslation } from "react-i18next";
import SettingsIcon from "@mui/icons-material/Settings";
import SelectFE from "../../../../../common/fieldEditors/SelectFE";
import { StudyMetadata } from "../../../../../../common/types";
import { editStudy } from "../../../../../../services/api/study";
import SwitchFE from "../../../../../common/fieldEditors/SwitchFE";
import {
  FIRST_JANUARY_OPTIONS,
  FormValues,
  WEEK_OPTIONS,
  YEAR_OPTIONS,
} from "./utils";
import BooleanFE from "../../../../../common/fieldEditors/BooleanFE";
import { useFormContext } from "../../../../../common/Form";
import useDebouncedEffect from "../../../../../../hooks/useDebouncedEffect";
import StringFE from "../../../../../common/fieldEditors/StringFE";
import NumberFE from "../../../../../common/fieldEditors/NumberFE";
import Fieldset from "../../../../../common/Fieldset";

interface Props {
  study: StudyMetadata;
  setDialog: React.Dispatch<React.SetStateAction<"thematicTrimming" | "">>;
}

function Fields(props: Props) {
  const { study, setDialog } = props;
  const studyVersion = Number(study.version);
  const [t] = useTranslation();
  const { control, setValue, watch, getValues } = useFormContext<FormValues>();
  const [buildingMode, firstDay, lastDay] = watch([
    "buildingMode",
    "firstDay",
    "lastDay",
  ]);

  useEffect(() => {
    if (buildingMode === "Derated") {
      setValue("nbYears", 1);
    }
  }, [buildingMode, setValue]);

  useDebouncedEffect(
    () => {
      if (firstDay > 0 && firstDay > lastDay) {
        setValue("lastDay", firstDay);
      }
    },
    { wait: 500, deps: [firstDay] }
  );

  useDebouncedEffect(
    () => {
      if (lastDay > 0 && lastDay < firstDay) {
        setValue("firstDay", lastDay);
      }
    },
    { wait: 500, deps: [lastDay] }
  );

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleDayValidation = (v: number) => {
    if (v < 1 || Number.isNaN(v)) {
      return "Minimum is 1";
    }
    if (getValues("firstDay") > getValues("lastDay")) {
      return false;
    }
    if (getValues("leapYear")) {
      return v <= 366 ? true : "Maximum is 366 for a leap year";
    }
    return v <= 365 ? true : "Maximum is 365 for a non-leap year";
  };

  ////////////////////////////////////////////////////////////////
  // Utils
  ////////////////////////////////////////////////////////////////

  const saveValue = R.curry((path: string, value) => {
    return editStudy(value, study.id, `settings/generaldata/${path}`);
  });

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <>
      <Fieldset legend={t("study.configuration.general.simulation")}>
        <SelectFE
          name="mode"
          label={t("study.configuration.general.mode")}
          options={["Economy", "Adequacy", "draft"]}
          control={control}
          rules={{
            onAutoSubmit: saveValue("general/mode"),
          }}
        />
        <NumberFE
          name="firstDay"
          label={t("study.configuration.general.firstDay")}
          variant="filled"
          control={control}
          rules={{
            deps: "lastDay",
            validate: handleDayValidation,
            onAutoSubmit: saveValue("general/simulation.start"),
          }}
        />
        <NumberFE
          name="lastDay"
          label={t("study.configuration.general.lastDay")}
          variant="filled"
          control={control}
          rules={{
            deps: "firstDay",
            validate: handleDayValidation,
            onAutoSubmit: saveValue("general/simulation.end"),
          }}
        />
      </Fieldset>
      <Fieldset legend={t("study.configuration.general.calendar")}>
        <StringFE
          name="horizon"
          label="Horizon"
          variant="filled"
          control={control}
          rules={{ onAutoSubmit: saveValue("general/horizon") }}
        />
        <SelectFE
          name="firstMonth"
          label={t("study.configuration.general.year")}
          options={YEAR_OPTIONS}
          control={control}
          rules={{
            onAutoSubmit: saveValue("general/first-month-in-year"),
          }}
        />
        <SelectFE
          name="firstWeekDay"
          label={t("study.configuration.general.week")}
          options={WEEK_OPTIONS}
          control={control}
          rules={{
            onAutoSubmit: saveValue("general/first.weekday"),
          }}
        />
        <SelectFE
          name="firstJanuary"
          label={t("study.configuration.general.firstDayOfYear")}
          options={FIRST_JANUARY_OPTIONS}
          control={control}
          rules={{ onAutoSubmit: saveValue("general/january.1st") }}
        />
        <SwitchFE
          name="leapYear"
          sx={{ flex: 1, flexBasis: "100%" }}
          label={t("study.configuration.general.leapYear")}
          control={control}
          rules={{
            deps: ["firstDay", "lastDay"],
            onAutoSubmit: saveValue("general/leapyear"),
          }}
        />
      </Fieldset>
      <Box sx={{ display: "flex" }}>
        <Fieldset
          legend={t("study.configuration.general.monteCarloScenarios")}
          sx={{
            flex: 1,
          }}
          contentProps={{
            sx: { flexDirection: "column" },
          }}
        >
          <NumberFE
            name="nbYears"
            label={t("global.number")}
            variant="filled"
            control={control}
            rules={{
              validate: (v) => {
                if (buildingMode === "Derated") {
                  return v === 1
                    ? true
                    : "Value must be 1 when building mode is derated";
                }
                if (v < 1) {
                  return "Minimum is 1";
                }
                return v <= 50000 ? true : "Maximum is 50000";
              },
              onAutoSubmit: saveValue("general/nbyears"),
            }}
          />
          <SelectFE
            name="buildingMode"
            label={t("study.configuration.general.buildingMode")}
            options={["Automatic", "Custom", "Derated"]}
            control={control}
            rules={{
              deps: "nbYears",
              onAutoSubmit: (v) => {
                if (v === "Derated") {
                  return saveValue("general/derated", true);
                }
                return Promise.all([
                  saveValue(
                    studyVersion >= 800
                      ? "general/custom-scenario"
                      : "general/custom-ts-numbers",
                    v === "Custom"
                  ),
                  saveValue("general/derated", false),
                ]);
              },
            }}
          />
          <BooleanFE
            name="selectionMode"
            label={t("study.configuration.general.selectionMode")}
            trueText="Custom"
            falseText="Automatic"
            control={control}
            rules={{ onAutoSubmit: saveValue("general/user-playlist") }}
          />
        </Fieldset>
        <Divider orientation="vertical" flexItem sx={{ mx: 2 }} />
        <Fieldset
          legend={t("study.configuration.general.outputProfile")}
          sx={{
            flex: 1,
          }}
          contentProps={{
            sx: { flexDirection: "column" },
          }}
        >
          <SwitchFE
            name="simulationSynthesis"
            label={t("study.configuration.general.simulationSynthesis")}
            control={control}
            rules={{ onAutoSubmit: saveValue("output/synthesis") }}
          />
          <SwitchFE
            name="yearByYear"
            label={t("study.configuration.general.yearByYear")}
            control={control}
            rules={{ onAutoSubmit: saveValue("general/year-by-year") }}
          />
          <SwitchFE
            name="mcScenario"
            label={t("study.configuration.general.mcScenario")}
            control={control}
            rules={{ onAutoSubmit: saveValue("output/storenewset") }}
          />
          {studyVersion >= 710 ? (
            <>
              <BooleanFE
                name="geographicTrimming"
                label={t("study.configuration.general.geographicTrimming")}
                trueText="Custom"
                falseText="None"
                control={control}
                rules={{
                  onAutoSubmit: saveValue("general/geographic-trimming"),
                }}
              />
              <Box>
                <BooleanFE
                  name="thematicTrimming"
                  label={t("study.configuration.general.thematicTrimming")}
                  trueText="Custom"
                  falseText="None"
                  control={control}
                  rules={{
                    onAutoSubmit: saveValue("general/thematic-trimming"),
                  }}
                />
                <Button
                  startIcon={<SettingsIcon />}
                  onClick={() => setDialog("thematicTrimming")}
                  disabled={!getValues("thematicTrimming")}
                >
                  {t("global.settings")}
                </Button>
              </Box>
            </>
          ) : (
            <SwitchFE
              name="filtering"
              label={t("study.configuration.general.filtering")}
              control={control}
              rules={{ onAutoSubmit: saveValue("general/filtering") }}
            />
          )}
        </Fieldset>
      </Box>
    </>
  );
}

export default Fields;
