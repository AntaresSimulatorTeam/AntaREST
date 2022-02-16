/* eslint-disable jsx-a11y/no-static-element-interactions */
import React from 'react';
import {
  makeStyles,
  createStyles,
  Theme,
  Button,
} from '@material-ui/core';
import AutoSizer from 'react-virtualized-auto-sizer';
import { FixedSizeList, areEqual, ListChildComponentProps } from 'react-window';
import ArrowRightIcon from '@material-ui/icons/ArrowRight';
import { XpansionCandidate } from './types';

const ROW_ITEM_SIZE = 60;

const useStyles = makeStyles((theme: Theme) =>
  createStyles({
    root: {
      width: '100%',
      minHeight: '100px',
      paddingLeft: theme.spacing(3),
      paddingTop: theme.spacing(1),
      paddingRight: theme.spacing(2),
      color: theme.palette.primary.main,
      display: 'flex',
      flexGrow: 1,
      flexShrink: 1,
      marginBottom: '76px',
    },
    list: {
      '&> div > div': {
        cursor: 'pointer',
        '&:hover': {
          textDecoration: 'underline',
        },
      },
    },
  }));

interface PropsType {
    candidates: Array<XpansionCandidate>;
    setSelectedItem: (item: XpansionCandidate) => void;
}

const Row = React.memo((props: ListChildComponentProps) => {
  const { data, index, style } = props;
  const { candidates, setSelectedItem } = data;
  const candidate = candidates[index];
  return (
    // eslint-disable-next-line jsx-a11y/click-events-have-key-events
    <div style={{ display: 'flex', justifyContent: 'space-evenly', alignItems: 'center', ...style }} onClick={() => setSelectedItem(candidate)}>
      {candidate.name}
      <ArrowRightIcon color="secondary" />
    </div>
  );
}, areEqual);

const NodeListing = (props: PropsType) => {
  const classes = useStyles();
  const { candidates, setSelectedItem } = props;

  return (
    <>
      <div className={classes.root}>
        {candidates.length > 0 && candidates && (
          <AutoSizer>
            { ({ height, width }) => {
              const idealHeight = ROW_ITEM_SIZE * candidates.length;
              return (
                <FixedSizeList
                  height={idealHeight > height ? height + ROW_ITEM_SIZE : idealHeight + ROW_ITEM_SIZE}
                  width={width}
                  itemCount={candidates.length}
                  itemSize={ROW_ITEM_SIZE}
                  itemData={{ candidates, setSelectedItem }}
                  className={classes.list}
                >
                  {Row}
                </FixedSizeList>
              );
            }
            }
          </AutoSizer>
        )}
      </div>
      <div>
        <Button>Settings</Button>
        <Button>Constraints</Button>
      </div>
    </>
  );
};

export default NodeListing;
