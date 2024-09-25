import { Box, BoxProps, Divider } from "@mui/material";
import * as RA from "ramda-adjunct";
import { mergeSxProp } from "../../utils/muiUtils";

interface FieldsetProps extends Omit<BoxProps, "component"> {
  legend?: string | React.ReactNode;
  children: React.ReactNode;
  contentProps?: BoxProps;
  fullFieldWidth?: boolean;
  fieldWidth?: number;
}

function Fieldset(props: FieldsetProps) {
  const {
    legend,
    children,
    sx,
    contentProps,
    fullFieldWidth = false,
    fieldWidth = 220,
    ...rest
  } = props;

  return (
    <Box
      {...rest}
      component="fieldset"
      sx={mergeSxProp(
        {
          border: "none",
          m: 0,
          p: 0,
          pb: 4,
          "> .MuiBox-root": {
            display: "flex",
            flexWrap: "wrap",
            gap: 2,
            ".MuiFormControl-root": {
              width: fullFieldWidth ? 1 : fieldWidth,
              m: 0,
            },
          },
          // Increase padding from the last child
          ".Form__Content > &:last-child": {
            pb: 2,
          },
          // Remove padding from the last child of the dialog content
          ".MuiDialogContent-root .Form__Content > &:last-child": {
            pb: 0,
          },
        },
        sx,
      )}
    >
      {legend && (
        <>
          {RA.isString(legend) ? (
            <Box component="legend">{legend}</Box>
          ) : (
            legend
          )}
          <Divider sx={{ mt: 1 }} />
        </>
      )}
      <Box {...contentProps} sx={mergeSxProp({ pt: 3 }, contentProps?.sx)}>
        {children}
      </Box>
    </Box>
  );
}

Fieldset.Break = function Break() {
  return <Box sx={{ flexBasis: "100%" }} />;
};

export default Fieldset;
