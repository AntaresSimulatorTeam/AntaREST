import React, { useState, useEffect } from 'react';
import { useSnackbar } from 'notistack';
import { useTranslation } from 'react-i18next';
import { UserInfo, BotDTO, IDType } from '../../../common/types';
import { deleteBot, getBots } from '../../../services/api/user';
import GenericSettingView from '../GenericSettingView';
import TokenPrinter from '../TokenPrinter';
import ConfirmationModal from '../../ui/ConfirmationModal';
import TokenCreationModal from './Modals/TokenCreationModal';
import TokenViewModal from './Modals/TokenViewModal';
import GenericListView from '../GenericListView';

interface PropTypes {
  user: UserInfo | undefined;
}

const TokenNormal = (props: PropTypes) => {
  const [t] = useTranslation();
  const { enqueueSnackbar } = useSnackbar();
  const { user } = props;

  const [filter, setFilter] = useState<string>('');
  const [idForDeletion, setIdForDeletion] = useState<IDType>(-1);
  const [tokenList, setTokenList] = useState<Array<BotDTO>>([]);
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

  const onDeleteClick = (id: IDType) => {
    setIdForDeletion(id);
    setOpenConfirmationModal(true);
  };

  const onWatchClick = (id: IDType) => {
    setCurrentBot(tokenList.find((item) => item.id === id));
    setOpenViewModal(true);
  };

  const manageTokenDeletion = async () => {
    // Implement "are you sure ?" modal. Then =>
    try {
      await deleteBot(idForDeletion as number);
      setTokenList(tokenList.filter((item) => item.id !== idForDeletion));
      enqueueSnackbar(t('settings:onTokenDeleteSuccess'), { variant: 'success' });
    } catch (e) {
      enqueueSnackbar(t('settings:onTokenDeleteError'), { variant: 'error' });
    }
    setIdForDeletion(-1);
    setOpenConfirmationModal(false);
  };

  const onNewTokenCreation = (newToken: string, newBot: BotDTO): void => {
    setLastCreatedToken(newToken);
    setTokenPrinterMode(true);

    if (user) {
      const bot: BotDTO = newBot;
      bot.owner = user.id;
      setTokenList(tokenList.concat(newBot));
    }
  };

  const onPrinterModeClosed = (): void => {
    setLastCreatedToken('');
    setTokenPrinterMode(false);
  };

  useEffect(() => {
    const init = async () => {
      try {
        if (user) {
          const data = await getBots(user.id);
          setTokenList(data);
        }
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
      <GenericListView
        data={tokenList}
        filter={filter}
        view
        onDeleteClick={onDeleteClick}
        onActionClick={onWatchClick}
      />

      {openCreationModal && (
        <TokenCreationModal
          open={openCreationModal} // Why 'openCreationModal &&' ? => Otherwise previous data are still present
          userGroups={user?.groups}
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

export default TokenNormal;
