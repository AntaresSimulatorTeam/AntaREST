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
          {RA.isString(title) ? (
            <Typography
              variant="h5"
              sx={{ fontSize: "1.25rem", fontWeight: 400, lineHeight: 1.334 }}
            >
              {title}
            </Typography>
          ) : (
            title
          )}
          <Divider sx={{ mt: 1 }} />
        </>
      )}
      <Box sx={{ pt: 2 }}>{children}</Box>
    </fieldset>
  );
}

export default Fieldset;
