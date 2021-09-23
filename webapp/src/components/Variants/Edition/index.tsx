import React, { useEffect, useState } from 'react';
import { makeStyles, createStyles, Theme, Button } from '@material-ui/core';
import { useTranslation } from 'react-i18next';
import { DropResult } from 'react-beautiful-dnd';
import { callbackify } from 'util';
import { CommandItem } from './CommandTypes';
import CommandListView from './DraggableCommands/CommandListView';
import { reorder, fromCommandDTOToCommandItem, onCommandsSave } from './utils';
import { getCommands } from '../../../services/api/variant';
import ConfirmationModal from '../../ui/ConfirmationModal';
import AddCommandModal from './AddCommandModal';

const useStyles = makeStyles((theme: Theme) => createStyles({
  root: {
    width: '100%',
    height: '100%',
    display: 'flex',
    flexFlow: 'column nowrap',
    justifyContent: 'flex-start',
    alignItems: 'center',
    boxSizing: 'border-box',
    padding: theme.spacing(1, 1),
    overflowY: 'hidden',
  },
  header: {
    width: '100%',
    height: '80px',
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
    boxSizing: 'border-box',
    overflowX: 'hidden',
    overflowY: 'auto',
    padding: theme.spacing(0),
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

interface CommandEvent {
    id?: string;
    action: 'updated' | 'deleted' | 'added' | 'moved';
    data?: any;
}

const EditionView = (props: PropTypes) => {
  const classes = useStyles();
  const [t] = useTranslation();
  const { studyId } = props;
  const [openConfirmationModal, setOpenConfirmationModal] = useState<boolean>(false);
  const [openAddCommandModal, setOpenAddCommandModal] = useState<boolean>(false);

  const fakeItemsYes: Array<CommandItem> = [{ id: 'command_id_1', name: 'Command 1', args: {}, action: 'ACTION_1' },
    { id: 'command_id_2', name: 'Command 2', args: {}, action: 'ACTION_2' },
    { id: 'command_id_3', name: 'Command 3', args: {}, action: 'ACTION_3' },
    { id: 'command_id_4', name: 'Command 4', args: {}, action: 'ACTION_4' },
    { id: 'command_id_5', name: 'Command 5', args: {}, action: 'ACTION_5' }];
  const fakeItems: Array<CommandItem> = [];
  const [commands, setCommands] = useState<Array<CommandItem>>(fakeItems);
  const [initCommands, setInitCommands] = useState<Array<CommandItem>>(fakeItems);

  const onDragEnd = ({ destination, source }: DropResult) => {
    // dropped outside the list
    if (!destination) return;
    const newItems = reorder(commands, source.index, destination.index);
    setCommands(newItems);
  };

  const onSave = async () => {
    try {
      const newCommandList: Array<CommandItem> = await onCommandsSave(studyId, initCommands, commands);
      setCommands(newCommandList);
      setInitCommands(newCommandList);
    } catch (e) {
      // Snackbar
      console.log(e);
    }
    setOpenConfirmationModal(false);
  };

  const onDelete = (index: number) => {
    setCommands((commandList) => commandList.filter((elm, idx) => idx !== index));
    console.log(index);
  };

  const onNewCommand = (name: string, action: string) => {
    setCommands(commands.concat([{ name, action, args: {} }]));
  };

  const onArgsUpdate = (index: number, args: object) => {
    let tmpCommand: Array<CommandItem> = [];
    tmpCommand = tmpCommand.concat(commands);
    tmpCommand[index].args = { ...args };
    setCommands(tmpCommand);
  };

  useEffect(() => {
    const init = async () => {
      try {
        let dtoItems = await getCommands(studyId);
        dtoItems = dtoItems.filter((elm) => elm.id !== undefined);
        console.log("COMMAND DTO: ", dtoItems);
        const commandItems = fromCommandDTOToCommandItem(dtoItems);
        console.log("COMMAND ITEMS: ", commandItems);
        setCommands(commandItems);
        setInitCommands(commandItems);
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
        <Button color="primary" variant="contained" style={{ marginRight: '10px' }} onClick={() => setOpenAddCommandModal(true)}>
          {t('variants:add')}
        </Button>
        <Button color="primary" variant="contained" onClick={() => setOpenConfirmationModal(true)}>
          {t('variants:save')}
        </Button>
      </div>
      <div className={classes.body}>
        <CommandListView items={commands} onDragEnd={onDragEnd} onDelete={onDelete} onArgsUpdate={onArgsUpdate} />
      </div>
      {openConfirmationModal && (
        <ConfirmationModal
          open={openConfirmationModal}
          title={t('main:confirmationModalTitle')}
          message={t('variants:confirmsave')}
          handleYes={onSave}
          handleNo={() => setOpenConfirmationModal(false)}
        />
      )}
      {openAddCommandModal && (
        <AddCommandModal
          open={openAddCommandModal}
          onClose={() => setOpenAddCommandModal(false)}
          onNewCommand={onNewCommand}
        />
      )}
    </div>
  );
};

export default EditionView;
