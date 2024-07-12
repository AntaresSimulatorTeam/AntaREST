import { Paper } from "@mui/material";

export interface ViewWrapperProps {
  children: React.ReactNode;
}

function ViewWrapper({ children }: ViewWrapperProps) {
  return (
    <Paper
      className="ViewWrapper"
      sx={{
        width: 1,
        height: 1,
        p: 2,
        ":has(.TabsView:first-child), :has(.TabWrapper:first-child)": {
          pt: 0,
        },
      }}
    >
      {children}
    </Paper>
  );
}

export default ViewWrapper;
