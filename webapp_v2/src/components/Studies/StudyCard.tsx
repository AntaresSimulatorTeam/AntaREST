import * as React from 'react';
import Card from '@mui/material/Card';
import CardActions from '@mui/material/CardActions';
import CardContent from '@mui/material/CardContent';
import Button from '@mui/material/Button';
import Typography from '@mui/material/Typography';
import { StudyMetadata } from '../../common/types';

interface Props {
  study: StudyMetadata
}

export default function StudyCard(props: Props) {
  const { study } = props;
  return (
    <Card variant="outlined" sx={{ minWidth: 275 }}>
      <CardContent>
        <Typography variant="h5" component="div" color="white" height="60px">
          {study.name}
        </Typography>
        <Typography sx={{ mb: 1.5 }} color="white">
          This is an example
        </Typography>
        <Typography variant="body2" color="white">
          of text content.
          <br />
          Real content is coming soon
        </Typography>
      </CardContent>
      <CardActions>
        <Button size="small" color="primary">Explore</Button>
      </CardActions>
    </Card>
  );
}
