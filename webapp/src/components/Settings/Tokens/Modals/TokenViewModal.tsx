import React, { useState, useEffect } from 'react';
import { createStyles,
  makeStyles,
  Theme,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow } from '@material-ui/core';
import { useSnackbar } from 'notistack';
import { useTranslation } from 'react-i18next';
import { BotDTO, BotIdentityDTO } from '../../../../common/types';
import { getBotInfos } from '../../../../services/api/user';
import InformationModal from '../../../ui/InformationModal';
import { roleToString } from '../../../../services/utils';

const useStyles = makeStyles((theme: Theme) =>
  createStyles({
    root: {
      width: '90%',
      padding: theme.spacing(2),
      boxSizing: 'border-box',
    },
    table: {
      width: '100%',
    },
    title: {
      fontWeight: 'bold',
    },
  }));

interface PropTypes {
  bot: BotDTO | undefined;
  open: boolean;
  onButtonClick: () => void;
}

const TokenViewModal = (props: PropTypes) => {
  const classes = useStyles();
  const [t] = useTranslation();
  const { enqueueSnackbar } = useSnackbar();
  const { bot, open, onButtonClick } = props;
  const [botInfos, setBotInfos] = useState<BotIdentityDTO|undefined>();

  useEffect(() => {
    const init = async () => {
      try {
        if (bot) {
          const res = await getBotInfos(bot.id);
          setBotInfos(res);
        }
      } catch (e) {
        enqueueSnackbar(t('settings:tokensError'), { variant: 'error' });
      }
    };
    init();
  }, [bot, t, enqueueSnackbar]);

  return (
    <InformationModal
      open={open}
      title={`Token${botInfos ? ` - ${botInfos.name}` : ''}`}
      onButtonClick={onButtonClick}
    >
      <TableContainer className={classes.root} component={Paper}>
        <Table className={classes.table} aria-label="simple table">
          <TableHead>
            <TableRow>
              <TableCell className={classes.title}>{t('settings:groupNameLabel')}</TableCell>
              <TableCell className={classes.title} align="right">Role</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {
                        !!botInfos &&
                        botInfos.roles.map((item) => (
                          <TableRow key={item.group_id}>
                            <TableCell component="th" scope="row">
                              {item.group_name}
                            </TableCell>
                            <TableCell align="right">{t(roleToString(item.type))}</TableCell>
                          </TableRow>
                        ))}
          </TableBody>
        </Table>
      </TableContainer>

    </InformationModal>
  );
};

export default TokenViewModal;
