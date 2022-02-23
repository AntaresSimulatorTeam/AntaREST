/* eslint-disable jsx-a11y/no-static-element-interactions */
import React, { useState } from 'react';
import {
  makeStyles,
  createStyles,
  Theme,
  Button,
} from '@material-ui/core';
import { useTranslation } from 'react-i18next';
import AutoSizer from 'react-virtualized-auto-sizer';
import { FixedSizeList, areEqual, ListChildComponentProps } from 'react-window';
import ArrowRightIcon from '@material-ui/icons/ArrowRight';
import ConfirmationModal from '../../ui/ConfirmationModal';
import { XpansionCandidate, XpansionSettings } from './types';

const ROW_ITEM_SIZE = 60;
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
    settings: XpansionSettings | undefined;
    constraints: string[] | string;
    selectedItem: XpansionCandidate | XpansionSettings | string | string[] | undefined;
    setSelectedItem: (item: XpansionCandidate | XpansionSettings | string | string[]) => void;
    deleteXpansion: () => void;
}

const Row = React.memo((props: ListChildComponentProps) => {
  const { data, index, style } = props;
  const { candidates, setSelectedItem, selectedItem } = data;
  const candidate = candidates[index];

  return (
    // eslint-disable-next-line jsx-a11y/click-events-have-key-events
    <div style={selectedItem && selectedItem.name === candidate.name ? { display: 'flex', justifyContent: 'space-evenly', alignItems: 'center', ...style, textDecoration: 'underline' } : { display: 'flex', justifyContent: 'space-evenly', alignItems: 'center', ...style }} onClick={() => setSelectedItem(candidate)}>
      {candidate.name}
      <ArrowRightIcon style={selectedItem && selectedItem.name === candidate.name ? { color: '#B26A00' } : { color: '#FF9800' }} />
    </div>
  );
}, areEqual);

const CandidateListing = (props: PropsType) => {
  const classes = useStyles();
  const [t] = useTranslation();
  const { candidates = [], settings, constraints, selectedItem, setSelectedItem, deleteXpansion } = props;
  const [openConfirmationModal, setOpenConfirmationModal] = useState<boolean>(false);

  return (
    <>
      <div className={classes.root}>
        {candidates && candidates.length > 0 && (
          <AutoSizer>
            { ({ height, width }) => {
              const idealHeight = ROW_ITEM_SIZE * candidates.length;
              return (
                <>
                  <FixedSizeList
                    height={idealHeight > height ? height + ROW_ITEM_SIZE - BUTTONS_SIZE : idealHeight}
                    width={width}
                    itemCount={candidates.length}
                    itemSize={ROW_ITEM_SIZE}
                    itemData={{ candidates, setSelectedItem, selectedItem }}
                    className={classes.list}
                  >
                    {Row}
                  </FixedSizeList>
                  <div className={classes.buttons} style={{ width }}>
                    <Button className={classes.button} size="small" onClick={() => { if (settings) { setSelectedItem(settings); } }}>Settings</Button>
                    <Button className={classes.button} size="small" onClick={() => setSelectedItem(constraints)}>Constraints</Button>
                    <Button className={classes.delete} size="small" onClick={() => setOpenConfirmationModal(true)}>Supprimer</Button>
                  </div>
                </>
              );
            }
            }
          </AutoSizer>
        )}
      </div>
      {openConfirmationModal && candidates && (
        <ConfirmationModal
          open={openConfirmationModal}
          title={t('main:confirmationModalTitle')}
          message="Êtes-vous sûr de vouloir supprimer Xpansion?"
          handleYes={() => { deleteXpansion(); setOpenConfirmationModal(false); }}
          handleNo={() => setOpenConfirmationModal(false)}
        />
      )}
    </>
  );
};

export default CandidateListing;
