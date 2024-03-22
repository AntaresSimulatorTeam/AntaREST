import { FormControlLabel, Switch, Typography } from "@mui/material";
import { ReactNode } from "react";
import { ConstraintElementData, ConstraintElementRoot } from "./style";
import { useTranslation } from "react-i18next";

interface ElementProps {
  left: ReactNode;
  right: ReactNode;
  operator?: string;
  isLink?: boolean;
  onToggleType?: () => void;
}

export default function ConstraintElement({
  isLink,
  left,
  right,
  operator,
  onToggleType,
}: ElementProps) {
  const { t } = useTranslation();

  return (
    <ConstraintElementRoot>
      <ConstraintElementData>
        {onToggleType !== undefined && (
          <FormControlLabel
            control={<Switch checked={isLink === true} />}
            onChange={(event, checked) => onToggleType()}
            label={isLink ? t("study.link") : t("study.cluster")}
            labelPlacement="bottom"
          />
        )}
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
