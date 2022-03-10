/* eslint-disable jsx-a11y/no-static-element-interactions */
import React from 'react';
import {
  makeStyles,
  createStyles,
  Theme,
  Typography,
  Box,
} from '@material-ui/core';
import AutoSizer from 'react-virtualized-auto-sizer';
import { FixedSizeList, areEqual, ListChildComponentProps } from 'react-window';
import ArrowRightIcon from '@material-ui/icons/ArrowRight';
import { XpansionCandidate, XpansionRenderView } from './types';

const ROW_ITEM_SIZE = 40;
const BUTTONS_SIZE = 40;

const useStyles = makeStyles((theme: Theme) =>
  createStyles({
    root: {
      width: '95%',
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
      marginBottom: theme.spacing(2),
      '&> div > div': {
        cursor: 'pointer',
        '&:hover': {
          textDecoration: 'underline',
          '&>svg': {
            color: `${theme.palette.secondary.dark} !important`,
          },
        },
      },
    },
    buttons: {
      position: 'absolute',
      right: '20px',
      bottom: '20px',
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'flex-end',
      color: theme.palette.secondary.dark,
    },
    button: {
      color: theme.palette.primary.main,
    },
    delete: {
      color: theme.palette.error.main,
    },
  }));

interface PropsType {
    candidates: Array<XpansionCandidate> | undefined;
    selectedItem: string;
    setSelectedItem: (item: string) => void;
    setView: (item: XpansionRenderView | undefined) => void;
}

const Row = React.memo((props: ListChildComponentProps) => {
  const { data, index, style } = props;
  const { candidates, setSelectedItem, selectedItem, setView } = data;
  const candidate = candidates[index];

  return (
    // eslint-disable-next-line jsx-a11y/click-events-have-key-events
    <Box style={selectedItem && selectedItem.name === candidate.name ? { display: 'flex', justifyContent: 'space-evenly', alignItems: 'center', ...style, textDecoration: 'underline' } : { display: 'flex', justifyContent: 'space-evenly', alignItems: 'center', ...style }} onClick={() => { setSelectedItem(candidate.name); setView(XpansionRenderView.candidate); }}>
      <Typography style={{ display: 'block', width: '200px', textOverflow: 'ellipsis', overflow: 'hidden', paddingLeft: '30px' }}>{candidate.name}</Typography>
      <ArrowRightIcon style={selectedItem && selectedItem.name === candidate.name ? { color: '#B26A00' } : { color: '#FF9800' }} />
    </Box>
  );
}, areEqual);

const CandidateListing = (props: PropsType) => {
  const classes = useStyles();
  const { candidates = [], selectedItem, setSelectedItem, setView } = props;

  return (
    <>
      <Box className={classes.root}>
        {candidates && candidates.length > 0 && (
          <AutoSizer>
            { ({ height, width }) => {
              const idealHeight = ROW_ITEM_SIZE * candidates.length;
              return (
                <FixedSizeList
                  height={idealHeight > height ? height + ROW_ITEM_SIZE - BUTTONS_SIZE : idealHeight}
                  width={width}
                  itemCount={candidates.length}
                  itemSize={ROW_ITEM_SIZE}
                  itemData={{ candidates, setSelectedItem, selectedItem, setView }}
                  className={classes.list}
                >
                  {Row}
                </FixedSizeList>
              );
            }
            }
          </AutoSizer>
        )}
      </Box>
    </>
  );
};

export default CandidateListing;
