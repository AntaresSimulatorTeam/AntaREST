import React, {useState, useEffect} from 'react';
import { createStyles, makeStyles, Theme, TextField } from '@material-ui/core';
import { useTranslation } from 'react-i18next';
import GenericModal from '../../../../components/Settings/GenericModal';
import {GroupDTO } from '../../../../common/types'


const useStyles = makeStyles((theme: Theme) => createStyles({
    infos: {
      flex: '1',
      width: '100%',
      display: 'flex',
      flexFlow: 'column nowrap',
      justifyContent: 'center',
      alignItems: 'center',
      padding: theme.spacing(2),
    },
    idFields: {
        width: '70%',
        height: '30px',
        boxSizing: 'border-box',
        margin: theme.spacing(2)
    }
  }));

interface PropTypes {
    open: boolean;
    onClose: () => void;
    onSave: (name: string) => void;
    group: GroupDTO | undefined;
};

const GroupModal = (props: PropTypes) => {

    const classes = useStyles();
    const [t] = useTranslation();
    const {open, group, onClose, onSave} = props;
    const [text, setText] = useState<string>('');

    const onChange = (event: React.ChangeEvent<{ value: unknown }>) => {
            setText(event.target.value as string)
        }

    useEffect(()=> {
        setText(!!group ? group.name : '');
    }, [group])

    return (

        <GenericModal 
        open={open}
        handleClose={onClose}
        handleSave={() => onSave(text)}
        title={!!group ? t('settings:group')+' - '+group.name : t('settings:newGroupTitle')}>
            <div className={classes.infos}>
                <TextField className={classes.idFields}
                           label={t('settings:groupNameLabel')}
                           variant="outlined"
                           onChange={onChange}
                           value={text} />
            </div>
      </GenericModal>       
    )

}

export default GroupModal;