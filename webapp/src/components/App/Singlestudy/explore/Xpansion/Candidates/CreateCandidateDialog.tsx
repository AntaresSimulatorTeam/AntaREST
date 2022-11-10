import { useState } from "react";
import { Button, ButtonGroup } from "@mui/material";
import { useTranslation } from "react-i18next";
import AddCircleIcon from "@mui/icons-material/AddCircle";
import * as R from "ramda";
import { LinkCreationInfoDTO } from "../../../../../../common/types";
import { XpansionCandidate } from "../types";
import FormDialog from "../../../../../common/dialogs/FormDialog";
import StringFE from "../../../../../common/fieldEditors/StringFE";
import Fieldset from "../../../../../common/Fieldset";
import SelectFE from "../../../../../common/fieldEditors/SelectFE";
import NumberFE from "../../../../../common/fieldEditors/NumberFE";
import { SubmitHandlerPlus } from "../../../../../common/Form/types";

interface PropType {
  open: boolean;
  links: Array<LinkCreationInfoDTO>;
  onClose: () => void;
  onSave: (candidate: XpansionCandidate) => void;
}

function CreateCandidateDialog(props: PropType) {
  const { open, links, onClose, onSave } = props;
  const [t] = useTranslation();
  const [isToggled, setToggle] = useState(true);

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleToggle = () => {
    setToggle(!isToggled);
  };

  const handleSubmit = (data: SubmitHandlerPlus<XpansionCandidate>) => {
    const values = R.omit(
      isToggled ? ["max-investment"] : ["unit-size", "max-units"],
      data.values
    );

    onSave(values);
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <FormDialog
      open={open}
      onCancel={onClose}
      title={t("xpansion.newCandidate")}
      titleIcon={AddCircleIcon}
      onSubmit={handleSubmit}
      config={{
        defaultValues: {
          name: "",
          link: "",
          "annual-cost-per-mw": 0,
          "unit-size": 0,
          "max-units": 0,
          "max-investment": 0,
        },
      }}
    >
      {({ control }) => (
        <>
          <Fieldset fullFieldWidth>
            <StringFE
              label={t("global.name")}
              name="name"
              control={control}
              sx={{ mx: 0 }}
            />
            <SelectFE
              label={t("xpansion.link")}
              options={links.map((link) => `${link.area1} - ${link.area2}`)}
              name="link"
              required
              control={control}
              fullWidth
            />
            <NumberFE
              label={t("xpansion.annualCost")}
              name="annual-cost-per-mw"
              control={control}
              sx={{ mx: 0 }}
            />
          </Fieldset>

          <Fieldset
            fullFieldWidth
            legend={
              isToggled
                ? `${t("xpansion.unitSize")} & ${t("xpansion.maxUnits")}`
                : t("xpansion.maxInvestments")
            }
          >
            <ButtonGroup
              disableElevation
              size="small"
              color="info"
              sx={{ py: 2 }}
            >
              <Button
                onClick={handleToggle}
                variant={!isToggled ? "outlined" : "contained"}
              >
                {`${t("xpansion.unitSize")} & ${t("xpansion.maxUnits")}`}
              </Button>
              <Button
                onClick={handleToggle}
                variant={isToggled ? "outlined" : "contained"}
              >
                {t("xpansion.maxInvestments")}
              </Button>
            </ButtonGroup>
            {isToggled ? (
              <>
                <NumberFE
                  label={t("xpansion.unitSize")}
                  name="unit-size"
                  control={control}
                  sx={{ mx: 0 }}
                />
                <NumberFE
                  label={t("xpansion.maxUnits")}
                  name="max-units"
                  control={control}
                  sx={{ mx: 0 }}
                />
              </>
            ) : (
              <NumberFE
                label={t("xpansion.maxInvestments")}
                name="max-investment"
                control={control}
                sx={{ mx: 0 }}
              />
            )}
          </Fieldset>
        </>
      )}
    </FormDialog>
  );
}

export default CreateCandidateDialog;
