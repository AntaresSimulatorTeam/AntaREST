import React, {useState, PropsWithChildren} from 'react';
import { createStyles, makeStyles, Theme, Button, Paper, Typography } from '@material-ui/core';
import InputLabel from '@material-ui/core/InputLabel';
import MenuItem from '@material-ui/core/MenuItem';
import FormHelperText from '@material-ui/core/FormHelperText';
import FormControl from '@material-ui/core/FormControl';
import Select from '@material-ui/core/Select';
import CloseIcon from '@material-ui/icons/Close';
import {} from '../../common/types'

const useStyles = makeStyles((theme: Theme) => createStyles({
  root: {
    width: '100%',
    height: '100%',
    display: 'flex',
    flexFlow: 'column nowrap',
    justifyContent: 'flex-start',
    alignItems: 'center',
    overflow: 'hidden'
  },
  groupsList: {
    //backgroundColor: 'red',
    width: '100%',
    height: '60px',
    flexFlow: 'row nowrap',
    justifyContent: 'flex-start',
    alignItems: 'center',
    overflow: 'hidden'
  },
  select: {
    margin: theme.spacing(2)
  },
  roleList:{
     width: '90%',
     flex: '1',
     overflow: 'auto',
     padding: theme.spacing(1),
     display: 'flex',
     flexFlow: 'column nowrap',
     alignItems: 'center'
  },
  role: {
      flex: '0 0 30px',
      width: '100%',
      margin: theme.spacing(0.1),
      padding: theme.spacing(1),
      boxSizing: 'border-box',
      display: 'flex',
      flexFlow: 'row nowrap',
      alignItems: 'center'
      //backgroundColor: 'red'
  },
  close: {
      color: theme.palette.error.main,
      marginLeft: theme.spacing(1),
      marginRight: theme.spacing(1)
  }
}));

interface Group {
    id: string
    name: string,
}

interface Role {
    groupId: string,
    role: number,
    userId: string
}

interface PropTypes {
    groupsList: Array<string>;
    selectedGroup: string;
    roleList: Array<string>;
    onChange: (value: string) => void;
    addGroup: () => void;
    deleteGroup: (name: string) => void;
    updateRoleType: (name : string, role: number) => void;
}


const GroupsAssignmentView = (props: PropsWithChildren<PropTypes>) => {

  const {groupsList, selectedGroup, onChange, roleList, addGroup, deleteGroup, updateRoleType} = props;
  const classes = useStyles();

  return (
    <div className={classes.root}>
        <div className={classes.groupsList}>
            <Select
            value={selectedGroup}
            onChange={(event: React.ChangeEvent<{ value: unknown }>) => onChange(event.target.value as string)}
            label="Groupname"
            className={classes.select}>
                {
                    groupsList.map((item) =>
                        <MenuItem value={item}>{item}</MenuItem>
                    )
                }
            </Select>
            <Button variant="contained"
                    color="primary" 
                    onClick={addGroup}>
                Add
            </Button>
        </div>
        <div className={classes.roleList}>
            {
                roleList.map((item) => 
                    <Paper className={classes.role}>
                            <CloseIcon className={classes.close} onClick={() => deleteGroup(item)} />
                            <Typography>{item}</Typography>
                    </Paper>
                )
            }
        </div>
    </div>

  );
};

export default GroupsAssignmentView;

