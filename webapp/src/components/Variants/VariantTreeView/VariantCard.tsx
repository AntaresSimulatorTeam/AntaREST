import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { Card, Grid, Theme } from '@material-ui/core';
import React, { CSSProperties } from 'react';
import { CustomNodeElementProps } from 'react-d3-tree/lib/types/common';

interface PropsType {
    rd3tProps: CustomNodeElementProps;
    theme: Theme;
    history: any;

}

const style = {
  root: (theme: Theme): CSSProperties => ({
    border: `1px solid ${theme.palette.primary.main}`,
    borderRadius: theme.shape.borderRadius,
    backgroundColor: 'white',
    width: '250px',
    height: '150px',
    boxSizing: 'border-box',
    display: 'flex',
    flexFlow: 'column nowrap',
    justifyContent: 'flex-start',
    alignItems: 'center',
  }),
  header: (): CSSProperties => ({
    width: '90%',
    display: 'flex',
    flexFlow: 'column nowrap',
    justifyContent: 'center',
    alignItems: 'flex-start',
  }),
  grid: (theme: Theme): CSSProperties => ({
    width: '90%',
    height: '100%',
    marginBottom: '1px',
    color: theme.palette.primary.main,
  }),
  infotxt: (theme: Theme): CSSProperties => ({
    marginLeft: theme.spacing(1),
    fontSize: '0.55em',
  }),
};
const VariantCard = (props: PropsType) => {
  const { rd3tProps, theme, history } = props;
  const { nodeDatum } = rd3tProps;
  if (nodeDatum.attributes === undefined) return <g />;

  const { name, attributes } = nodeDatum;
  const { id, owner, version, creationDate, modificationDate } = attributes;

  return (
    <g>
      <foreignObject width={250} height={150} x={-125} y={-75}>
        <Card onClick={() => history.push(`/study/${id}/variants`)} style={style.root(theme)}>
          <div style={style.header()}>
            <h3 style={{ fontSize: '0.8em', color: theme.palette.primary.main, marginBottom: '2px' }}>{name}</h3>
            <h3 style={{ fontSize: '0.7em', color: 'gray', marginTop: '0px' }}>{id}</h3>
          </div>
          <Grid container spacing={2} style={style.grid(theme)}>
            <Grid item xs={6}>
              <FontAwesomeIcon icon="user" />
              <span style={style.infotxt(theme)}>{owner}</span>
            </Grid>
            <Grid item xs={6}>
              <FontAwesomeIcon icon="clock" />
              <span style={style.infotxt(theme)}>
                {creationDate}
              </span>
            </Grid>
            <Grid item xs={6}>
              <FontAwesomeIcon icon="code-branch" />
              <span style={style.infotxt(theme)}>{version}</span>
            </Grid>
            <Grid item xs={6}>
              <FontAwesomeIcon icon="history" />
              <span style={style.infotxt(theme)}>
                {modificationDate}
              </span>
            </Grid>
          </Grid>
        </Card>
      </foreignObject>
    </g>
  );
};

export default VariantCard;
