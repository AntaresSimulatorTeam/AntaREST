import React, { useState } from 'react';
import { createStyles, makeStyles, TextField, Theme } from '@material-ui/core';
import { useTranslation } from 'react-i18next';
import DeleteIcon from '@material-ui/icons/Delete';
import CancelIcon from '@material-ui/icons/Cancel';
import CreateIcon from '@material-ui/icons/Create';
import CheckCircleIcon from '@material-ui/icons/CheckCircle';

const useStyles = makeStyles((theme: Theme) => createStyles({
  root: {
    display: 'flex',
    flexFlow: 'row nowrap',
    justifyContent: 'flex-start',
    alignItems: 'center',
    width: '100%',
    height: '50px',
    marginBottom: theme.spacing(2),
  },
  editableField: {
    flex: '1',
    margin: theme.spacing(1),
  },
  editionIcon: {
    display: 'flex',
    flexFlow: 'row nowrap',
    justifyContent: 'flex-start',
    alignItems: 'center',
    flex: '1',
  },
  checkIcon: {
    color: theme.palette.primary.main,
    '&:hover': {
      color: theme.palette.success.main,
    },
  },
  cancelIcon: {
    color: theme.palette.primary.main,
    marginLeft: theme.spacing(1),
    '&:hover': {
      color: theme.palette.error.main,
    },
  },
  createIcon: {
    color: theme.palette.primary.main,
    '&:hover': {
      color: theme.palette.secondary.main,
    },
  },
}));

export type Metadata = {key: string; value: string; editStatus: boolean};

interface PropTypes {
  metadata: Metadata;
  index: number;
  onConfirmation: (newMetadata: Metadata, index: number) => void;
  editToogle: (index: number) => void;
  onDeletion: (index: number) => void;
}

export function KeyValue(props: PropTypes) {
  // eslint-disable-next-line react/destructuring-assignment
  const { metadata, index, onConfirmation, editToogle, onDeletion } = props;
  const { editStatus } = metadata;
  const classes = useStyles();
  const [t] = useTranslation();
  const [key, setKey] = useState<string>(metadata.key);
  const [value, setValue] = useState<string>(metadata.value);
  const [isKeyEmpty, setKeyEmpty] = useState<boolean>(!key.replace(/\s/g, ''));
  const [isValueEmpty, setValueEmpty] = useState<boolean>(!value.replace(/\s/g, ''));
  const onCancel = () => {
    editToogle(index);
    if (metadata.key && metadata.value) {
      setKey(metadata.key);
      setValue(metadata.value);
    } else {
      onDeletion(index);
    }
  };

  const onKeyChange = (str: string) => {
    setKeyEmpty(!str.replace(/\s/g, ''));
    setKey(str);
  };

  const onValueChange = (str: string) => {
    setValueEmpty(!str.replace(/\s/g, ''));
    setValue(str);
  };

  return (
    <div className={classes.root}>

      <TextField
        className={classes.editableField}
        size="small"
        value={key}
        onChange={(event) => onKeyChange(event.target.value as string)}
        label={t('data:key')}
        InputProps={{
          readOnly: !editStatus,
        }}
        error={isKeyEmpty}
        helperText={isKeyEmpty ? t('data:emptyString') : ''}
      />
      <TextField
        className={classes.editableField}
        size="small"
        value={value}
        onChange={(event) => onValueChange(event.target.value as string)}
        label={t('data:value')}
        InputProps={{
          readOnly: !editStatus,
        }}
        error={isValueEmpty}
        helperText={isValueEmpty ? t('data:emptyString') : ''}
      />
      <div className={classes.editionIcon}>
        {
              editStatus ? (
                <>
                  <CheckCircleIcon
                    className={classes.checkIcon}
                    onClick={() => onConfirmation({ key, value, editStatus }, index)}
                  />
                  <CancelIcon
                    className={classes.cancelIcon}
                    onClick={() => onCancel()}
                  />
                </>
              ) : (
                <>
                  <CreateIcon
                    className={classes.createIcon}
                    onClick={() => editToogle(index)}
                  />
                  <DeleteIcon
                    className={classes.cancelIcon}
                    onClick={() => onDeletion(index)}
                  />
                </>
              )}
      </div>
    </div>
  );
}
