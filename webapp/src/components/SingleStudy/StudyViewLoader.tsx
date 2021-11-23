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

const StudyViewLoader = () => {
  const classes = useStyles();

  return (
    <div className={classes.contentloader}>
      <ContentLoader
        speed={2}
        backgroundColor="#dedede"
        foregroundColor="#ececec"
        className={classes.contentloader1}
      >
        <rect x="1%" y="2%" rx="2" ry="2" width="30%" height="85%" />
        <rect x="32%" y="2%" rx="2" ry="2" width="67%" height="41%" />
        <rect x="32%" y="45%" rx="2" ry="2" width="67%" height="42%" />
      </ContentLoader>
      <ContentLoader
        speed={2}
        backgroundColor="#B9B9B9"
        foregroundColor="#ececec"
        className={classes.contentloader2}
      >
        <rect x="1%" y="2%" rx="2" ry="2" width="30%" height="4%" />
        <rect x="32%" y="2%" rx="2" ry="2" width="67%" height="4%" />
        <rect x="32%" y="45%" rx="2" ry="2" width="67%" height="4%" />

        <rect x="3%" y="9%" rx="2" ry="2" width="20%" height="3%" />
        <rect x="3%" y="13%" rx="2" ry="2" width="19%" height="2%" />

        <rect x="3%" y="18%" rx="2" ry="2" width="11%" height="3%" />
        <rect x="3%" y="22%" rx="2" ry="2" width="8%" height="2%" />
        <rect x="12%" y="22%" rx="2" ry="2" width="8%" height="2%" />
        <rect x="3%" y="25%" rx="2" ry="2" width="10%" height="2%" />
        <rect x="14%" y="25%" rx="2" ry="2" width="8%" height="2%" />
        <rect x="3%" y="28%" rx="2" ry="2" width="4%" height="2%" />
        <rect x="8%" y="28%" rx="2" ry="2" width="2%" height="2%" />

        <rect x="3%" y="34%" rx="2" ry="2" width="7%" height="3%" />
        <rect x="3%" y="38%" rx="2" ry="2" width="6%" height="2%" />
        <rect x="3%" y="41%" rx="2" ry="2" width="11%" height="2%" />

        <rect x="12%" y="52%" rx="2" ry="2" width="7%" height="6%" />
        <rect x="12%" y="59%" rx="2" ry="2" width="7%" height="6%" />

        <rect x="25%" y="83%" rx="2" ry="2" width="5%" height="2%" />
      </ContentLoader>
    </div>
  );
};

export default StudyViewLoader;
