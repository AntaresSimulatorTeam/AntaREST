import React, { useState } from 'react';
import { Box, Card, CardActions, CardContent, Button, Typography } from '@mui/material';
import { styled } from '@mui/material/styles';
import StarPurple500OutlinedIcon from '@mui/icons-material/StarPurple500Outlined';
import StarOutlineOutlinedIcon from '@mui/icons-material/StarOutlineOutlined';
import ScheduleOutlinedIcon from '@mui/icons-material/ScheduleOutlined';
import UpdateOutlinedIcon from '@mui/icons-material/UpdateOutlined';
import PersonOutlineIcon from '@mui/icons-material/PersonOutline';
import MoreVertIcon from '@mui/icons-material/MoreVert';
import { GenericInfo, StudyMetadata } from '../../common/types';

interface Props {
  study: StudyMetadata
  favorite: boolean;
  onFavoriteClick: (value: GenericInfo) => void;
}

const TinyText = styled(Typography)(({ theme }) => ({
  fontSize: '16px',
  color: theme.palette.text.secondary,
}));

export default function StudyCard(props: Props) {
  const { study , favorite, onFavoriteClick} = props;

  const handleFavoriteClick = () => {
    onFavoriteClick({id: study.id, name: study.name});
  }

  return (
    <Card variant="outlined" sx={{ minWidth: 275 }}>
      <CardContent>
        <Box width="100%" height="60px" display="flex" flexDirection="row" justifyContent="space-between" p={0.5}>
          <Typography sx={{ width: '90%' }} noWrap variant="h5" component="div" color="white">
            {study.name}
          </Typography>
          {favorite ? <StarPurple500OutlinedIcon sx={{ cursor: 'pointer' }} onClick={handleFavoriteClick} color="primary" /> :
                      <StarOutlineOutlinedIcon sx={{ cursor: 'pointer' }} onClick={handleFavoriteClick} color="primary" />
          }
        </Box>
        <Box width="100%" display="flex" flexDirection="row" justifyContent="space-between" mt={1}>
          <Box display="flex" flexDirection="row" justifyContent="flex-start" alignItems="center">
            <ScheduleOutlinedIcon sx={{ color: 'text.secondary', mr: 1 }} />
            <TinyText>
              {study.creationDate}
            </TinyText>
          </Box>
          <Box display="flex" flexDirection="row" justifyContent="flex-start" alignItems="center">
            <UpdateOutlinedIcon sx={{ color: 'text.secondary', mr: 1 }} />
            <TinyText>
              10 min ago
            </TinyText>
          </Box>
        </Box>
        <Box width="100%" display="flex" flexDirection="row" justifyContent="flex-start" alignItems="center">
            <PersonOutlineIcon sx={{ color: 'text.secondary', mr: 1 }} />
            <TinyText>
                {study.owner.name}
            </TinyText>
        </Box>        
        <Typography sx={{ textAlign: 'justify', mt: 2 }}>
          This is a fake content.
          <br />
          Real content is coming soon
        </Typography>
      </CardContent>
      <CardActions>
        <Button size="small" color="primary">Explore</Button>
        <Button size="small" color="primary" sx={{ width: 'auto', minWidth: 0, p: 0 }}>
          <MoreVertIcon />
        </Button>
      </CardActions>
    </Card>
  );
}
