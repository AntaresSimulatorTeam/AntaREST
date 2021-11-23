import React from 'react';
import ContentLoader from 'react-content-loader';
import { makeStyles, createStyles } from '@material-ui/core';

const useStyles = makeStyles(() =>
  createStyles({
    contentloader: {
      width: '100%',
      height: '100%',
    },
    contentloader1: {
      width: '100%',
      height: '100%',
      zIndex: 0,
      position: 'absolute',
    },
    contentloader2: {
      width: '100%',
      height: '100%',
      zIndex: 10,
      position: 'absolute',
    },
  }));

const DataViewLoader = () => {
  const classes = useStyles();

  return (
    <div className={classes.contentloader}>
      <ContentLoader
        speed={2}
        backgroundColor="#dedede"
        foregroundColor="#ececec"
        className={classes.contentloader1}
      >
        <rect x="8%" y="3%" rx="2" ry="2" width="64%" height="6%" />
        <rect x="8%" y="9.4%" rx="2" ry="2" width="64%" height="6%" />
        <rect x="8%" y="15.8%" rx="2" ry="2" width="64%" height="6%" />
        <rect x="8%" y="22.2%" rx="2" ry="2" width="64%" height="6%" />
        <rect x="8%" y="28.6%" rx="2" ry="2" width="64%" height="6%" />
      </ContentLoader>
      <ContentLoader
        speed={2}
        backgroundColor="#B9B9B9"
        foregroundColor="#ececec"
        className={classes.contentloader2}
      >
        <rect x="8%" y="3%" rx="4" ry="4" width=".5%" height="6%" />
        <rect x="8%" y="9.4%" rx="4" ry="4" width=".5%" height="6%" />
        <rect x="8%" y="15.8%" rx="4" ry="4" width=".5%" height="6%" />
        <rect x="8%" y="22.2%" rx="4" ry="4" width=".5%" height="6%" />
        <rect x="8%" y="28.6%" rx="4" ry="4" width=".5%" height="6%" />

        <rect x="9.7%" y="4.5%" rx="4" ry="4" width="5%" height="3%" />
        <rect x="9.7%" y="10.9%" rx="4" ry="4" width="7%" height="3%" />
        <rect x="9.7%" y="17.3%" rx="4" ry="4" width="3%" height="3%" />
        <rect x="9.7%" y="23.7%" rx="4" ry="4" width="10%" height="3%" />
        <rect x="9.7%" y="30.1%" rx="4" ry="4" width="6%" height="3%" />

        <rect x="65.4%" y="4.75%" rx="2" ry="2" width="1.5%" height="2.75%" />
        <rect x="67.6%" y="4.75%" rx="2" ry="2" width="1.5%" height="2.75%" />
        <rect x="69.8%" y="4.75%" rx="2" ry="2" width="1.5%" height="2.75%" />

        <rect x="65.4%" y="11.15%" rx="2" ry="2" width="1.5%" height="2.75%" />
        <rect x="67.6%" y="11.15%" rx="2" ry="2" width="1.5%" height="2.75%" />
        <rect x="69.8%" y="11.15%" rx="2" ry="2" width="1.5%" height="2.75%" />

        <rect x="65.4%" y="17.55%" rx="2" ry="2" width="1.5%" height="2.75%" />
        <rect x="67.6%" y="17.55%" rx="2" ry="2" width="1.5%" height="2.75%" />
        <rect x="69.8%" y="17.55%" rx="2" ry="2" width="1.5%" height="2.75%" />

        <rect x="65.4%" y="23.95%" rx="2" ry="2" width="1.5%" height="2.75%" />
        <rect x="67.6%" y="23.95%" rx="2" ry="2" width="1.5%" height="2.75%" />
        <rect x="69.8%" y="23.95%" rx="2" ry="2" width="1.5%" height="2.75%" />

        <rect x="65.4%" y="30.35%" rx="2" ry="2" width="1.5%" height="2.75%" />
        <rect x="67.6%" y="30.35%" rx="2" ry="2" width="1.5%" height="2.75%" />
        <rect x="69.8%" y="30.35%" rx="2" ry="2" width="1.5%" height="2.75%" />
      </ContentLoader>
    </div>
  );
};

export default DataViewLoader;
