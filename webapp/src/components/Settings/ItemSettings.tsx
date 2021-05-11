import React from 'react';
import { makeStyles, createStyles, Theme, Typography, Button } from '@material-ui/core';
import CreateIcon from '@material-ui/icons/Create';
import DeleteIcon from '@material-ui/icons/Delete';


const useStyles = makeStyles((theme: Theme) => createStyles({
    root: {
        flex: 'none',
        width: '80%',
        display: 'flex',
        padding: '10px 20px',
        flexFlow: 'row nowrap',
        justifyContent: 'flex-start',
        borderRadius: '30px',
        backgroundColor: theme.palette.primary.main,
        '&:hover':{
            backgroundColor: theme.palette.primary.dark,
        },
        color: 'white',
        margin: '2px',
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
        color: 'red'
    },
    createIcon:
    {
        color: theme.palette.primary.light,
    }
}));
  
interface PropTypes {
    id: number,
    key: number,
    value: string,
    onDeleteCLick: (id: number) => void,
    onUpdateClick: (id : number) => void
}

const ItemSettings = (props: PropTypes) => {

    const classes = useStyles();
    const {id, value, onDeleteCLick, onUpdateClick} = props;

    return (
    <div className={classes.root}>
        <Typography>{value}</Typography>
        <div className={classes.iconsContainer}>
            <Button onClick={() => onUpdateClick(id)}>
                <CreateIcon className={classes.createIcon} />
            </Button>
            <Button onClick={() => onDeleteCLick(id)}>
                <DeleteIcon className={classes.deleteIcon}/>
            </Button>
        </div>
    </div>
    );

}

export default ItemSettings
