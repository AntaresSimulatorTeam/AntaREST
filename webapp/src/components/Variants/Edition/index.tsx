import React, { useEffect, useState } from 'react';
import { makeStyles, createStyles, Theme, Button } from '@material-ui/core';
import { useTranslation } from 'react-i18next';
import { DropResult } from 'react-beautiful-dnd';
import { CommandItem } from './CommandTypes';
import CommandListView from './DraggableCommands/CommandListView';
import { reorder, fromCommandDTOToCommandItem, fromCommandItemToCommandDTO } from './utils';
import { CommandDTO } from '../../../common/types';
import { appendCommands, getCommands } from '../../../services/api/variant';

const useStyles = makeStyles((theme: Theme) => createStyles({
  root: {
    width: '100%',
    height: '100%',
    display: 'flex',
    flexFlow: 'column nowrap',
    justifyContent: 'flex-start',
    alignItems: 'center',
    boxSizing: 'border-box',
    padding: theme.spacing(2, 1),
    // backgroundColor: 'red',
  },
  header: {
    width: '100%',
    flex: '0 0 10%',
    // backgroundColor: 'blue',
    display: 'flex',
    flexFlow: 'row nowrap',
    justifyContent: 'flex-end',
    alignItems: 'center',
    boxSizing: 'border-box',
  },
  body: {
    width: '100%',
    flex: 1,
    borderRadius: theme.shape.borderRadius,
    border: `1px solid ${theme.palette.primary.main}`,
    // backgroundColor: 'green',
    boxSizing: 'border-box',
    overflowX: 'hidden',
    overflowY: 'auto',
  },
  addButton: {
    color: theme.palette.primary.main,
    '&:hover': {
      color: theme.palette.secondary.main,
    },
  },
}));

interface PropTypes {
    studyId: string;
}

const EditionView = (props: PropTypes) => {
  const classes = useStyles();
  const [t] = useTranslation();
  const { studyId } = props;

  const fakeItems: Array<CommandItem> = [{ name: 'Command 1', args: 'args 1', action: 'ACTION_1' },
    { name: 'Command 2', args: 'args 2', action: 'ACTION_2' },
    { name: 'Command 3', args: 'args 3', action: 'ACTION_3' },
    { name: 'Command 4', args: 'args 4', action: 'ACTION_4' },
    { name: 'Command 5', args: 'args 5', action: 'ACTION_5' }];
  const [commands, setCommands] = useState<Array<CommandItem>>(fakeItems);

  const onDragEnd = ({ destination, source }: DropResult) => {
    // dropped outside the list
    if (!destination) return;
    const newItems = reorder(commands, source.index, destination.index);
    setCommands(newItems);
  };

  const onSave = async () => {
    try {
    // Convert CommandItem to CommandDTO
      const dtoItems: Array<CommandDTO> = fromCommandItemToCommandDTO(commands);
      // Call await appendComands
      await appendCommands(studyId, dtoItems);
    } catch (e) {
      // Snackbar
      console.log(e);
    }
  };

  useEffect(() => {
    const init = async () => {
      try {
        const dtoItems = await getCommands(studyId);
        setCommands(fromCommandDTOToCommandItem(dtoItems));
      } catch (e) {
        // Snackbar
        console.log(e);
      }
    };

    init();
  }, [studyId]);

  return (
    <div className={classes.root}>
      <div className={classes.header}>
        <Button color="primary" variant="contained" style={{ marginRight: '10px' }}>
          {t('variants:add')}
        </Button>
        <Button color="primary" variant="contained" onClick={() => onSave()}>
          {t('variants:save')}
        </Button>
      </div>
      <div className={classes.body}>
        <CommandListView items={commands} onDragEnd={onDragEnd} />
      </div>
    </div>
  );
};

export default EditionView;
