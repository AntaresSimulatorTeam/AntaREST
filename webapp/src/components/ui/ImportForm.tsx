import React from 'react';
import { useForm } from 'react-hook-form';
import { Button, createStyles, makeStyles, Theme } from '@material-ui/core';

const useStyles = makeStyles((theme: Theme) =>
  createStyles({
    root: {
      marginTop: theme.spacing(2),
      marginBottom: theme.spacing(2),
      display: 'flex',
      alignItems: 'center',
    },
    button: {
      width: '100px',
      height: '30px',
      border: `2px solid ${theme.palette.primary.main}`,
      '&:hover': {
        border: `2px solid ${theme.palette.secondary.main}`,
        color: theme.palette.secondary.main,
      },
      fontWeight: 'bold',
    },
    input: {
      width: '200px',
      marginLeft: theme.spacing(2),
      marginRight: theme.spacing(2),
    },
  }));

interface Inputs {
    file: FileList;
}

interface PropTypes {
  onImport: (file: File) => void;
  text: string;
}

const ImportForm = (props: PropTypes) => {
  const { text, onImport } = props;
  const classes = useStyles();
  const { register, handleSubmit } = useForm<Inputs>();

  const onSubmit = (data: Inputs) => {
    if (data.file && data.file.length === 1) {
      onImport(data.file[0]);
    }
  };

  return (
    <form className={classes.root} onSubmit={handleSubmit(onSubmit)}>
      <Button className={classes.button} type="submit" variant="outlined" color="primary">{text}</Button>
      <input className={classes.input} type="file" name="file" ref={register({ required: true })} />
    </form>
  );
};

export default ImportForm;
