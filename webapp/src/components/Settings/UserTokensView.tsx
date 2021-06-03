import React, {useState, useEffect, Fragment} from 'react';
import { makeStyles, createStyles, Theme, Typography, Button } from '@material-ui/core';
import VisibilityIcon from '@material-ui/icons/Visibility';
import DeleteIcon from '@material-ui/icons/Delete';
import {List, ListItem, ListItemText, Collapse}  from '@material-ui/core';
import ExpandLess from '@material-ui/icons/ExpandLess';
import ExpandMore from '@material-ui/icons/ExpandMore';
import {UserToken } from '../../common/types';



const useStyles = makeStyles((theme: Theme) => createStyles({
    root: {
        flex: 'none',
        width: '80%',
        display: 'flex',
        padding: theme.spacing(0),
        flexFlow: 'column nowrap',
        justifyContent: 'flex-start',
        color: theme.palette.primary.main,
        margin: theme.spacing(3),
    },
    botList:{
        display: 'flex',
        paddingLeft: theme.spacing(4),
        flexFlow: 'column nowrap',
        justifyContent: 'flex-start',
    },
    userItem: {
        backgroundColor: 'white',
        margin: theme.spacing(1),
        border: `1px solid ${theme.palette.primary.main}`
    },
    botItem: {
        display: 'flex',
        padding: theme.spacing(1),
        flexFlow: 'row nowrap',
        justifyContent: 'flex-start',
        color: theme.palette.primary.main,
        backgroundColor: 'white',
        margin: theme.spacing(1)
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
    seeIcon:
    {
        color: theme.palette.primary.main,
    }
}));

interface PropTypes {
    data: Array<UserToken>;
    filter: string;
    onDeleteClick: (userId: number, botId: number) => void;
    onWatchClick : (userId: number, botId: number) => void;
}

const UserTokensView = (props: PropTypes) => {

    const classes = useStyles();
    const {data, filter, onDeleteClick, onWatchClick} = props;
    const [toogleList, setToogleList] = useState<Array<boolean>>([]);

    const onButtonChange = (index: number) => {
        if(index >= 0 && index < toogleList.length)
        {
            const tmpList = ([] as Array<boolean>).concat(toogleList);
            tmpList[index] = !tmpList[index];
            setToogleList(tmpList);
        }
    }

    const matchFilter = (input: string) : boolean => {
      //Very basic search => possibly modify
      return (input.search(filter) >= 0);
    }

    useEffect(() => {
        const initToogleList : Array<boolean> = [];
        for(let i = 0; i < data.length; i++)
            initToogleList.push(false);
        setToogleList(initToogleList); 
    }, [data]);

    return (
        <List
        component="nav"
        aria-labelledby="nested-list-subheader"
        className={classes.root}
        >
            {
                data.map((userItem, index) => {
                    return (
                        <Fragment key={userItem.user.id}>
                            <ListItem className={classes.userItem}
                                    button
                                    onClick={() => onButtonChange(index)}
                                    >
                                    <ListItemText primary={userItem.user.name} />
                                        {toogleList[index] ? <ExpandLess /> : <ExpandMore />}
                            </ListItem>
                            <Collapse in={toogleList[index]} timeout="auto" unmountOnExit>
                                <List component="div"
                                    disablePadding
                                    className={classes.botList}>
                                    {
                                        userItem.bots.map((botItem) => {
                                            return (
                                                matchFilter(botItem.name) &&
                                                <ListItem key={botItem.id} className={classes.botItem}>
                                                    <Typography>{botItem.name}</Typography>
                                                    <div className={classes.iconsContainer}>
                                                        <Button onClick={() => onWatchClick(userItem.user.id, botItem.id)}>
                                                            <VisibilityIcon className={classes.seeIcon} />
                                                        </Button>
                                                        <Button onClick={() => onDeleteClick(userItem.user.id, botItem.id)}>
                                                            <DeleteIcon className={classes.deleteIcon}/>
                                                        </Button>
                                                    </div>                                                    
                                                </ListItem> 
                                            )                                       
                                        })
                                    }
                                </List>
                            </Collapse>
                        </Fragment>
                    )

                })               
            }
        </List> 
    );

}

export default UserTokensView