import React, {useState, useEffect} from 'react';
import { createStyles, makeStyles, Theme, TextField } from '@material-ui/core';
//import { useSnackbar } from 'notistack';
//import { useTranslation } from 'react-i18next';
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
    group: {
        isNewGroup: boolean;
        item: GroupDTO | undefined;
    };
};

const GroupModal = (props: PropTypes) => {

    const classes = useStyles();
    //const [t] = useTranslation();
    //const { enqueueSnackbar } = useSnackbar();
    const {open, group, onClose} = props;
    const [text, setText] = useState<string>('');

    const onChange = (event: React.ChangeEvent<{ value: unknown }>) => {
            setText(event.target.value as string)
        }

    const onSave = (newName: string) => {
            //1) If isNewGroup => 
            if(group.isNewGroup)
            {
              // Call backend here
              console.log('Creating new group => '+newName);
            }
            else
            {
               // Call backend here
               console.log('Updating group name => '+newName);         
            }
    }

    useEffect(()=> {
        setText(group.item ? group.item.name : '');
    }, [group])

    return (

        <GenericModal 
        open={open}
        handleClose={onClose}
        handleSave={() => onSave(text)}
        title={group.isNewGroup ? 'New Group': (group.item ? group.item.name+' group' : '')}>
            <div className={classes.infos}>
                <TextField className={classes.idFields}
                           label="Group name"
                           variant="outlined"
                           onChange={onChange}
                           value={text} />
            </div>
      </GenericModal>       
    )

}

export default GroupModal;


