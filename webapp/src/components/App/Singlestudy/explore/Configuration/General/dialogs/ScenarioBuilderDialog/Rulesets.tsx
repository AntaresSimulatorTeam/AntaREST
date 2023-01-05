import { InputLabel, IconButton, Box } from "@mui/material";
import EditIcon from "@mui/icons-material/Edit";
import DeleteIcon from "@mui/icons-material/Delete";
import { useTranslation } from "react-i18next";
import { useContext } from "react";
import SelectFE from "../../../../../../../common/fieldEditors/SelectFE";
import ConfigContext from "./ConfigContext";

function Rulesets() {
  const { config, currentRuleset, setCurrentRuleset } =
    useContext(ConfigContext);
  const { t } = useTranslation();

  return (
    <Box
      sx={{
        display: "flex",
        alignItems: "center",
        gap: 1,
      }}
    >
      <InputLabel>
        {t("study.configuration.general.mcScenarioBuilder.ruleset")}
      </InputLabel>
      <SelectFE
        options={Object.keys(config)}
        size="small"
        variant="outlined"
        value={currentRuleset}
        onChange={(event) => setCurrentRuleset(event.target.value as string)}
      />
      <IconButton>
        <EditIcon />
      </IconButton>
      <IconButton>
        <DeleteIcon />
      </IconButton>
    </Box>
  );
}

export default Rulesets;
