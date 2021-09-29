import React, { useRef } from 'react';
import { ButtonBase, createStyles, makeStyles, Theme } from '@material-ui/core';
import CloudUploadOutlinedIcon from '@material-ui/icons/CloudUploadOutlined';

const useStyles = makeStyles((theme: Theme) =>
  createStyles({
    root: {
      display: 'flex',
      alignItems: 'center',
    },
    importIcon: {
      width: '24px',
      height: 'auto',
      cursor: 'pointer',
      color: theme.palette.primary.main,
      margin: theme.spacing(0, 0.5),
      '&:hover': {
        color: theme.palette.secondary.main,
      },
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
  onImport: (json: object) => void;
}

const CommandImportButton = (props: PropTypes) => {
  const { onImport } = props;
  const classes = useStyles();
  // const formRef = useRef(null);
  // const { register, handleSubmit, getValues } = useForm<Inputs>();
  const inputRef = useRef<HTMLInputElement | null>(null);

  const onButtonClick = () => {
    if (inputRef.current) {
      inputRef.current.click();
    }
  };

  const onInputClick = (e: React.MouseEvent<HTMLInputElement | MouseEvent>) => {
    if (e && e.target) {
      const element = e.target as HTMLInputElement;
      element.value = '';
    }
  };

  const handleChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    e.preventDefault();
    const reader = new FileReader();
    reader.onload = async (ev: ProgressEvent<FileReader>) => {
      if (ev.target) {
        const text = (ev.target.result);
        onImport(JSON.parse(text as string));
      }
    };
    if (e.target && e.target.files) reader.readAsText(e.target.files[0]);
  };

  return (
    <div className={classes.root}>
      <ButtonBase type="submit" style={{ width: 'auto', height: 'auto' }} onClick={onButtonClick}>
        <CloudUploadOutlinedIcon className={classes.importIcon} />
      </ButtonBase>
      <input style={{ display: 'none' }} type="file" name="file" accept="application/json" onChange={(e) => handleChange(e)} onClick={(e) => onInputClick(e)} ref={(e) => { inputRef.current = e; }} />
    </div>
  );
};

export default CommandImportButton;
