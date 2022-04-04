import React, { useEffect, useState } from "react";
import { Box, Typography, List, ListItem, ListItemText } from "@mui/material";
import { scrollbarStyle, STUDIES_SIDE_NAV_WIDTH } from "../../theme";
import StudyTree from "./StudyTree";
import { GenericInfo, StudyMetadata } from "../../common/types";
import { buildStudyTree, StudyTreeNode } from "./utils";

interface Props {
  studies: Array<StudyMetadata>;
  folder: string;
  setFolder: (folder: string) => void;
  favorite: Array<GenericInfo>;
}

function SideNav(props: Props) {
  const { studies, folder, setFolder, favorite } = props;
  const [tree, setTree] = useState<StudyTreeNode>(buildStudyTree(studies));
  useEffect(() => {
    setTree(buildStudyTree(studies));
  }, [studies]);
  return (
    <Box
      flex={`0 0 ${STUDIES_SIDE_NAV_WIDTH}px`}
      height="100%"
      display="flex"
      flexDirection="column"
      justifyContent="flex-start"
      alignItems="flex-start"
      boxSizing="border-box"
      p={2}
      sx={{ overflowX: "hidden", overflowY: "auto", ...scrollbarStyle }}
    >
      <Typography sx={{ color: "grey.400" }}>Favorites</Typography>
      <List sx={{ width: "100%" }}>
        {favorite.map((elm) => (
          <ListItem
            key={elm.id}
            sx={{
              width: "100%",
              m: 0,
              py: 0,
              px: 1,
              cursor: "pointer",
              "&:hover": {
                bgcolor: "primary.outlinedHoverBackground",
              },
            }}
          >
            <ListItemText primary={elm.name} />
          </ListItem>
        ))}
      </List>
      <Typography sx={{ color: "grey.400" }}>Exploration</Typography>
      <StudyTree tree={tree} folder={folder} setFolder={setFolder} />
    </Box>
  );
}

export default SideNav;
