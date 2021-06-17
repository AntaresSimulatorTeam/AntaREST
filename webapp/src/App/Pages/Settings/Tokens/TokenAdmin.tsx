import React, { useState, useEffect } from 'react';
import { useSnackbar } from 'notistack';
import { useTranslation } from 'react-i18next';
import { UserInfo, UserToken, BotDTO } from '../../../../common/types';
import { getAdminTokenList, deleteBot } from '../../../../services/api/user';
import GenericSettingView from '../../../../components/Settings/GenericSettingView';
import UserTokensView from '../../../../components/Settings/UserTokensView';
import TokenPrinter from '../../../../components/Settings/TokenPrinter';
import ConfirmationModal from '../../../../components/ui/ConfirmationModal';
import TokenCreationModal from './Modals/TokenCreationModal';
import TokenViewModal from './Modals/TokenViewModal';

interface PropTypes {
  user: UserInfo | undefined;
}

const TokenAdmin = (props: PropTypes) => {
  const [t] = useTranslation();
  const { enqueueSnackbar } = useSnackbar();
  const { user } = props;
  const [filter, setFilter] = useState<string>('');
  const [idForDeletion, setIdForDeletion] = useState<any>(undefined);
  const [tokenList, setTokenList] = useState<Array<UserToken>>([]);
  const [currentBot, setCurrentBot] = useState<BotDTO|undefined>();
  const [lastCreatedToken, setLastCreatedToken] = useState<string>('');
  const [tokenPrinterMode, setTokenPrinterMode] = useState<boolean>(false);
  const [openCreationModal, setOpenCreationModal] = useState<boolean>(false);
  const [openViewModal, setOpenViewModal] = useState<boolean>(false);
  const [openConfirmationModal, setOpenConfirmationModal] = useState<boolean>(false);

  const createNewToken = () => {
    setCurrentBot(undefined);
    setOpenCreationModal(true);
  };

  const onDeleteClick = (userId: number, botId: number) => {
    setIdForDeletion({ userId, botId });
    setOpenConfirmationModal(true);
  };

  const onWatchClick = (userId: number, botId: number) => {
    const token = tokenList.find((item) => item.user.id === userId);
    if (token) {
      setCurrentBot(token.bots.find((item) => item.id === botId));
      setOpenViewModal(true);
    }
  };

  const manageTokenDeletion = async () => {
    // Implement "are you sure ?" modal. Then =>
    try {
      if (idForDeletion) {
        await deleteBot(idForDeletion.botId);
        const tmpList = ([] as Array<UserToken>).concat(tokenList);
        const userIndex = tmpList.findIndex((item) => item.user.id === idForDeletion.userId);

        if (userIndex >= 0) {
          tmpList[userIndex].bots = tmpList[userIndex].bots.filter((item) => item.id !== idForDeletion.botId);
          setTokenList(tmpList);
        }
        enqueueSnackbar(t('settings:onTokenDeleteSuccess'), { variant: 'success' });
      }
    } catch (e) {
      enqueueSnackbar(t('settings:onTokenDeleteError'), { variant: 'error' });
    }
    setIdForDeletion(undefined);
    setOpenConfirmationModal(false);
  };

  const onNewTokenCreation = (newToken: string, newBot: BotDTO): void => {
    setLastCreatedToken(newToken);
    setTokenPrinterMode(true);

    if (user) {
      const bot: BotDTO = newBot;
      bot.owner = user.id;
      const tmpList = ([] as Array<UserToken>).concat(tokenList);
      const userIndex = tmpList.findIndex((item) => item.user.id === user.id);

      if (userIndex >= 0) {
        tmpList[userIndex].bots.push(bot);
        setTokenList(tmpList);
      }
    }
  };

  const onPrinterModeClosed = (): void => {
    setLastCreatedToken('');
    setTokenPrinterMode(false);
  };

  useEffect(() => {
    const init = async () => {
      try {
        const data = await getAdminTokenList();
        setTokenList(data);
      } catch (e) {
        enqueueSnackbar(t('settings:tokensError'), { variant: 'error' });
      }
    };
    init();
    return () => {
      setTokenList([]);
    };
  }, [user, t, enqueueSnackbar]);

  if (tokenPrinterMode) {
    return (
      <TokenPrinter
        token={lastCreatedToken}
        onButtonClick={onPrinterModeClosed}
      />
    );
  }

  return (
    <GenericSettingView
      searchFilter={(input: string) => setFilter(input)}
      placeholder={t('settings:tokensSearchbarPlaceholder')}
      buttonValue={t('settings:createToken')}
      onButtonClick={() => createNewToken()}
    >

      <UserTokensView
        data={tokenList}
        filter={filter}
        onDeleteClick={onDeleteClick}
        onWatchClick={onWatchClick}
      />

      {openCreationModal && (
        <TokenCreationModal
          open={openCreationModal} // Why 'openCreationModal &&' ? => Otherwise previous data are still present
          onNewTokenCreation={onNewTokenCreation}
          onClose={() => setOpenCreationModal(false)}
        />
      )}
      {openConfirmationModal && (
        <ConfirmationModal
          open={openConfirmationModal}
          title={t('main:confirmationModalTitle')}
          message={t('settings:deleteTokenConfirmation')}
          handleYes={manageTokenDeletion}
          handleNo={() => setOpenConfirmationModal(false)}
        />
      )}
      {openViewModal && (
        <TokenViewModal
          open={openViewModal}
          bot={currentBot}
          onButtonClick={() => setOpenViewModal(false)}
        />
      )}
    </GenericSettingView>
  );
};

export default TokenAdmin;
