import React from 'react';
import { makeStyles, createStyles, Theme, Typography, Button, Paper } from '@material-ui/core';
import CreateIcon from '@material-ui/icons/Create';
import DeleteIcon from '@material-ui/icons/Delete';
import VisibilityIcon from '@material-ui/icons/Visibility';
import {IDType } from '../../common/types'


const useStyles = makeStyles((theme: Theme) => createStyles({
    root: {
        flex: 'none',
        width: '80%',
        display: 'flex',
        padding: theme.spacing(2),
        flexFlow: 'row nowrap',
        justifyContent: 'flex-start',
        color: theme.palette.primary.main,
        margin: theme.spacing(1),
    },
    iconsContainer:
    {
        flex: '1',
        display: 'flex',
        flexFlow: 'row nowrap',
        justifyContent: 'flex-end',
        alignItems: 'center'

    },
    deleteIcon:
    {
        color: theme.palette.error.main
    },
    actionIcon:
    {
        color: theme.palette.primary.main,
    }
}));
  
interface PropTypes {
    id: IDType,
    key: IDType,
    value: string,
    view: boolean;
    onDeleteCLick: (id: IDType) => void,
    onActionClick: (id : IDType) => void
}

const ItemSettings = (props: PropTypes) => {

    const classes = useStyles();
    const {id, value, view, onDeleteCLick, onActionClick} = props;

    return (
    <Paper className={classes.root}>
        <Typography>{value}</Typography>
        <div className={classes.iconsContainer}>
            <Button onClick={() => onActionClick(id)}>
            {
                view ? 
                (<VisibilityIcon className={classes.actionIcon} />) : 
                (<CreateIcon className={classes.actionIcon} />)
            
            }
            </Button>
            <Button onClick={() => onDeleteCLick(id)}>
                <DeleteIcon className={classes.deleteIcon}/>
            </Button>
        </div>
    </Paper>
    );

}

export default ItemSettings