import React, { useState } from 'react';
import {
  makeStyles,
  createStyles,
  Theme,
  TextField,
} from '@material-ui/core';
import GenericModal from '../../ui/GenericModal';

const useStyles = makeStyles((theme: Theme) =>
  createStyles({
    name: {
      margin: theme.spacing(2),
    },
    positions: {
      margin: theme.spacing(2),
      display: 'flex',
      justifyContent: 'center',
      alignItems: 'center',
    },
    posX: {
      width: '130px',
    },
    posY: {
      width: '130px',
    },
    color: {
      margin: theme.spacing(2),
    },
  }));

interface PropType {
    open: boolean;
    onClose: () => void;
    onSave: (name: string, posX: number, posY: number, color: string) => void;
}

const CreateAreaModal = (props: PropType) => {
  const classes = useStyles();
  const { open, onClose, onSave } = props;
  const [name, setName] = useState<string>('');
  const [posX, setPosX] = useState<number>(0);
  const [posY, setPosY] = useState<number>(0);
  const [color, setColor] = useState<string>('rgb(0, 0, 0)');

  return (
    <GenericModal
      open={open}
      handleClose={onClose}
      handleSave={() => onSave(name, posX, posY, color)}
      title="New area"
    >
      <div className={classes.name}>
        <TextField
          label="Nom"
          variant="outlined"
          onChange={(event) => setName(event.target.value as string)}
          value={name}
          size="small"
        />
      </div>
      <div className={classes.positions}>
        <TextField
          className={classes.posX}
          label="Position X"
          type="number"
          variant="outlined"
          size="small"
          onChange={(event) => setPosX(parseInt(event.target.value, 10) as number)}
          value={posX}
        />
        <TextField
          className={classes.posY}
          label="Position Y"
          type="number"
          variant="outlined"
          size="small"
          onChange={(event) => setPosY(parseInt(event.target.value, 10) as number)}
          value={posY}
        />
      </div>
      <div className={classes.color}>
        <TextField
          label="Couleur"
          variant="outlined"
          onChange={(event) => setColor(event.target.value as string)}
          value={color}
          size="small"
        />
      </div>
    </GenericModal>
  );
};

export default CreateAreaModal;
