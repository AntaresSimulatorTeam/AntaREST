import { Box, Divider, Typography } from "@mui/material";
import * as RA from "ramda-adjunct";

interface FieldsetProps {
  title?: string | React.ReactNode;
  children: React.ReactNode;
  style?: React.CSSProperties;
}

function Fieldset(props: FieldsetProps) {
  const { title, children, style } = props;

  return (
    <fieldset style={{ border: "none", margin: 0, padding: 0, ...style }}>
      {title && (
        <>
          <legend style={{ padding: 0 }}>
            {RA.isString(title) ? (
              <Typography variant="h5">{title}</Typography>
            ) : (
              title
            )}
          </legend>
          <Divider />
        </>
      )}
      <Box sx={{ py: 2 }}>{children}</Box>
    </fieldset>
  );
}

export default Fieldset;
