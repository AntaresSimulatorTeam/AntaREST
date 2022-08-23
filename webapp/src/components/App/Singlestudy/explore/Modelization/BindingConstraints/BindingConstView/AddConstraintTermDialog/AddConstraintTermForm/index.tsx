import { useState } from "react";
import { Box, Button, Typography } from "@mui/material";
import AddCircleOutlineRoundedIcon from "@mui/icons-material/AddCircleOutlineRounded";
import { useTranslation } from "react-i18next";
import { AllClustersAndLinks } from "../../../../../../../../../common/types";
import OptionsList from "./OptionsList";
import NumberFE from "../../../../../../../../common/fieldEditors/NumberFE";
import {
  ControlPlus,
  useFormContext,
} from "../../../../../../../../common/Form";
import { ConstraintItemRoot } from "../../ConstraintTerm/style";
import { ConstraintElement } from "../../ConstraintTerm";
import { ConstraintType } from "../../utils";

interface ItemProps {
  options: AllClustersAndLinks;
  control: ControlPlus<ConstraintType, any>;
}

export function ConstraintTermForm(props: ItemProps) {
  const { options, control } = props;
  const [t] = useTranslation();
  const [isLink, setIsLink] = useState(true);
  const [isOffset, setIsOffset] = useState(false);

  return (
    <ConstraintItemRoot>
      <ConstraintElement
        title="Weight"
        isLink={isLink}
        onToggleType={() => setIsLink((value) => !value)}
        left={
          <NumberFE
            name="weight"
            label={t("study.modelization.bindingConst.weight")}
            variant="filled"
            control={control}
            rules={{
              required: t("form.field.required") as string,
            }}
          />
        }
        right={
          <Box sx={{ display: "flex", alignItems: "center" }}>
            <OptionsList isLink={isLink} list={options} control={control} />
          </Box>
        }
      />
      {isOffset ? (
        <>
          <Typography sx={{ mx: 1 }}>x</Typography>
          <ConstraintElement
            title="Offset"
            operator="+"
            left={<Typography>t</Typography>}
            right={
              <NumberFE
                name="offset"
                label={t("study.modelization.bindingConst.offset")}
                variant="filled"
                control={control}
                rules={{
                  required: t("form.field.required") as string,
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
          sx={{ mx: 1 }}
          onClick={() => setIsOffset(true)}
        >
          {t("study.modelization.bindingConst.offset")}
        </Button>
      )}
    </ConstraintItemRoot>
  );
}

interface Props {
  options: AllClustersAndLinks;
}

export default function AddConstraintTermForm(props: Props) {
  const { options } = props;
  const { control } = useFormContext<ConstraintType>();

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <Box
      sx={{
        display: "flex",
        justifyContent: "center",
        alignItems: "center",
        width: "100%",
      }}
    >
      <ConstraintTermForm options={options} control={control} />
    </Box>
  );
}
