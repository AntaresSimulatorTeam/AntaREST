import React, { useEffect, useState } from 'react';
import { Box, Typography } from '@mui/material';
import { scrollbarStyle, STUDIES_SIDE_NAV_WIDTH } from '../../theme';
import StudyTree from './StudyTree';
import { StudyMetadata } from '../../common/types';
import { buildStudyTree, StudyTreeNode } from './utils';

interface Props {
  studies: Array<StudyMetadata>
  folder: string;
  setFolder: (folder: string) => void;
};

function SideNav(props: Props) {
  const { studies, folder, setFolder } = props;
  const [tree, setTree] = useState<StudyTreeNode>(buildStudyTree(studies));
  useEffect(() => {
    setTree(buildStudyTree(studies));
  }, [studies])
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
      sx={{ overflowX: 'hidden', overflowY: 'auto', ...scrollbarStyle }}
    >
      <Typography sx={{ color: 'grey.400' }}>Favorites</Typography>
      <Typography sx={{ color: 'grey.400' }}>Exploration</Typography>
      <StudyTree tree={tree} folder={folder} setFolder={setFolder} />
    </Box>
  );
}

export default SideNav;
