import { useEffect, useState } from "react";
import { useNavigate } from "react-router";
import { Box, Typography, List, ListItem, ListItemText } from "@mui/material";
import { useTranslation } from "react-i18next";
import { scrollbarStyle, STUDIES_SIDE_NAV_WIDTH } from "../../theme";
import StudyTree from "./StudyTree";
import { StudyMetadata } from "../../common/types";
import { buildStudyTree, StudyTreeNode } from "./utils";
import { StudiesState } from "../../redux/ducks/studies";

interface Props {
  studies: Array<StudyMetadata>;
  folder: string;
  setFolder: (folder: string) => void;
  favorites: StudiesState["favorites"];
}

function SideNav(props: Props) {
  const navigate = useNavigate();
  const { studies, folder, setFolder, favorites } = props;
  const { t } = useTranslation();
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
      <Typography sx={{ color: "grey.400" }}>
        {t("global:studies.favorites")}
      </Typography>
      <List sx={{ width: "100%" }}>
        {favorites.map((fav) => (
          <ListItem
            key={fav}
            onClick={() => navigate(`/studies/${fav}`)}
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
            <ListItemText
              primary={studies.find((study) => study.id === fav)?.name}
            />
          </ListItem>
        ))}
      </List>
      <Typography sx={{ color: "grey.400" }}>Exploration</Typography>
      <StudyTree tree={tree} folder={folder} setFolder={setFolder} />
    </Box>
  );
}

export default SideNav;
