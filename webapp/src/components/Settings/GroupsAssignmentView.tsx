import React from 'react';
import { createStyles, makeStyles, Theme, Button, Paper, Typography } from '@material-ui/core';
import MenuItem from '@material-ui/core/MenuItem';
import Select from '@material-ui/core/Select';
import CloseIcon from '@material-ui/icons/Close';
import {GroupDTO, RoleType, RoleDTO } from '../../common/types'

const useStyles = makeStyles((theme: Theme) => createStyles({
  root: {
    width: '100%',
    height: '100%',
    display: 'flex',
    flexFlow: 'column nowrap',
    justifyContent: 'flex-start',
    alignItems: 'center',
    marginTop: theme.spacing(2),
    overflow: 'hidden'
  },
  titleBox: {
    width: '100%',
    paddingLeft: theme.spacing(2)
  },
  title: {
    color: theme.palette.primary.main,
  },
  groupsList: {
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
  },
  close: {
      color: theme.palette.error.main,
      marginLeft: theme.spacing(1),
      marginRight: theme.spacing(1)
  }
}));


interface PropTypes {
    groupsList: Array<GroupDTO>;
    selectedGroupId: string;
    roleList: Array<RoleDTO>;
    onChange: (group_id: string) => void;
    addRole: (groupId: string) => void;
    deleteRole: (group_id: string) => void;
    updateRoleType: (group_id : string, type: RoleType) => void;
}


const GroupsAssignmentView = (props: PropTypes) => {

  const {groupsList, selectedGroupId, onChange, roleList, addRole, deleteRole, updateRoleType} = props;
  const classes = useStyles();

  return (
    <div className={classes.root}>
        <div className={classes.titleBox}>
            <Typography className={classes.title}>Permissions</Typography>
        </div>
        <div className={classes.groupsList}>
            <Select
            value={selectedGroupId}
            onChange={(event: React.ChangeEvent<{ value: unknown }>) => onChange(event.target.value as string)}
            label="Groupname"
            className={classes.select}>
                {
                    groupsList.map((item) =>
                        <MenuItem key={item.id} value={item.id}>{item.name}</MenuItem>
                    )
                }
            </Select>
            <Button variant="contained"
                    color="primary" 
                    onClick={() => addRole(selectedGroupId)}>
                Add
            </Button>
        </div>
        <div className={classes.roleList}>
            {
                roleList.map((item) => 
                    <Paper key={item.group_id} className={classes.role}>
                            <CloseIcon className={classes.close} onClick={() => deleteRole(item.group_id)} />
                            <Typography>{(groupsList.find((elm) => item.group_id === elm.id) as GroupDTO).name }</Typography>
                            <Select
                                value={item.type}
                                onChange={(event: React.ChangeEvent<{ value: unknown }>) => updateRoleType(item.group_id, event.target.value as RoleType)}
                                label="Groupname"
                                className={classes.select}>

                                <MenuItem value={10}>READER</MenuItem>
                                <MenuItem value={20}>WRITTER</MenuItem>
                                <MenuItem value={30}>RUNNER</MenuItem>
                                <MenuItem value={40}>ADMIN</MenuItem>
                            </Select>
                    </Paper>
                )
            }
        </div>
    </div>

  );
};

export default GroupsAssignmentView;

