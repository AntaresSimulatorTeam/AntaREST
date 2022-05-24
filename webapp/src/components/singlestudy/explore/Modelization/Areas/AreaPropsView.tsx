import { Box } from "@mui/material";
import PropertiesView from "../../../../common/PropertiesView";

function AreaPropsView() {
  return (
    <PropertiesView
      mainContent={
        <Box
          width="100%"
          flexGrow={1}
          flexShrink={1}
          display="flex"
          flexDirection="column"
          justifyContent="flex-start"
          alignItems="center"
          bgcolor="black"
        >
          Hello
        </Box>
      }
      secondaryContent={<div />}
      onSearchFilterChange={(e) => console.log(e as string)}
      onAdd={() => console.log("ADD")}
    />
  );
}

export default AreaPropsView;
