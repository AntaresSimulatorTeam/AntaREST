import React from 'react';
import { makeStyles, createStyles, Theme, Typography, Button, Paper } from '@material-ui/core';
import CreateIcon from '@material-ui/icons/Create';
import DeleteIcon from '@material-ui/icons/Delete';
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
        margin: theme.spacing(3),
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
    createIcon:
    {
        color: theme.palette.primary.main,
    }
}));
  
interface PropTypes {
    id: IDType,
    key: IDType,
    value: string,
    onDeleteCLick: (id: IDType) => void,
    onUpdateClick: (id : IDType) => void
}

const ItemSettings = (props: PropTypes) => {

    const classes = useStyles();
    const {id, value, onDeleteCLick, onUpdateClick} = props;

    return (
    <Paper className={classes.root}>
        <Typography>{value}</Typography>
        <div className={classes.iconsContainer}>
            <Button onClick={() => onUpdateClick(id)}>
                <CreateIcon className={classes.createIcon} />
            </Button>
            <Button onClick={() => onDeleteCLick(id)}>
                <DeleteIcon className={classes.deleteIcon}/>
            </Button>
        </div>
    </Paper>
    );

}

export default ItemSettings