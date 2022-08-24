import { FormControlLabel, Switch, Typography } from "@mui/material";
import { ReactNode } from "react";
import {
  ConstraintElementData,
  ConstraintElementHeader,
  ConstraintElementRoot,
} from "./style";

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
