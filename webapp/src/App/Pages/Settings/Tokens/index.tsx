import React, { useState, useEffect } from 'react';
import { connect, ConnectedProps } from 'react-redux';
import { useSnackbar } from 'notistack';
import { useTranslation } from 'react-i18next';
import {isUserAdmin} from '../../../../services/utils'
import { AppState } from '../../../reducers';
import GenericSettingView from '../../../../components/Settings/GenericSettingView';
import ItemSettings from '../../../../components/Settings/ItemSettings';
import { getTokens, getTokensWithOwner, deleteToken} from '../../../../services/api/user';
import {TokenDTO, IDType } from '../../../../common/types';
import TokenModal from './TokenModal'
import ConfirmationModal from '../../../../components/ui/ConfirmationModal'

const mapState = (state: AppState) => ({
    user: state.auth.user,
  });

const connector = connect(mapState);
type ReduxProps = ConnectedProps<typeof connector>;
type PropTypes = ReduxProps;

const TokensSettings = (props: PropTypes) => {

    const [t] = useTranslation();
    const { enqueueSnackbar } = useSnackbar();
    const [tokenList, setTokenList] = useState<Array<TokenDTO>>([]);
    const [idForDeletion, setIdForDeletion] = useState<IDType>(-1);
    const [filter, setFilter] = useState<string>("");
    const {user} = props;

    // Token modal
    const [openModal, setOpenModal] = useState<boolean>(false);
    const [openConfirmationModal, setOpenConfirmationModal] = useState<boolean>(false);
    const [currentToken, setCurrentToken] = useState<TokenDTO|undefined>();

    const createNewToken = () => {
          setCurrentToken(undefined);
          setOpenModal(true);
    }

    const onUpdateClick = (id: IDType) : void => {
      setCurrentToken(tokenList.find((item)=> item.id === id));
      setOpenModal(true);
  }

  const onDeleteClick = (id: IDType) => {
    setIdForDeletion(id);
    setOpenConfirmationModal(true);
  }

  const manageTokenDeletion = async () => {
      try
      {
        const res = await deleteToken(idForDeletion as number);
        setTokenList(tokenList.filter((item) => item.id !== idForDeletion));
        console.log(res);
        enqueueSnackbar(t('settings:onTokenDeleteSuccess'), { variant: 'success' });
      }
      catch(e)
      {
        enqueueSnackbar(t('settings:onTokenDeleteError'), { variant: 'error' });
      }
      setIdForDeletion(-1);
      setOpenConfirmationModal(false);
  }

    const onModalClose = () => {
      setOpenModal(false);
    }

    const onNewTokenCreation = (newToken : TokenDTO) : void => {
      setTokenList(tokenList.concat(newToken));
      setCurrentToken(newToken);
    }

    const onUpdateToken = (id: number, name : string, isAuthor: boolean) : void => {
      const tmpList = ([] as TokenDTO[]).concat(tokenList);
      const index = tmpList.findIndex((item) => item.id === id)
      if(index >= 0)
      {
        tmpList[index].name = name;
        tmpList[index].isAuthor = isAuthor;
        setTokenList(tmpList);
      }  
    }

    const matchFilter = (input: string) : boolean => {
      //Very basic search => possibly modify
      return (input.search(filter) >= 0);
    }

    useEffect(() => {
      const init = async () =>{

        try {
            const tokens = (!!user && !isUserAdmin(user)) ? await getTokensWithOwner(user.id) : await getTokens();
            console.log('Tokens ');
            console.log(tokens);
            setTokenList(tokens);         
        } catch (e) {
          enqueueSnackbar(t('settings:tokensError'), { variant: 'error' });
        }
  
      }
      init();
    }, [user, t, enqueueSnackbar]);

    return (
      <GenericSettingView searchFilter={(input: string) => setFilter(input)}
                                         placeholder={t('settings:tokensSearchbarPlaceholder')}
                                         buttonValue={t('settings:createToken')}
                                         onButtonClick={() => createNewToken()}>
                          {
                            tokenList.map((item) => 
                            matchFilter(item.name) && 
                                          <ItemSettings key={item.id}
                                            id={item.id}
                                            value={String(item.name)}
                                            onDeleteCLick={onDeleteClick}
                                            onUpdateClick={onUpdateClick} />)
                          }
        {openModal && <TokenModal  open={openModal}
                                   tokenInfos={currentToken}
                                   onNewTokenCreation={onNewTokenCreation}
                                   onUpdateToken={onUpdateToken}
                                   onClose={onModalClose} />}
        {openConfirmationModal && <ConfirmationModal open={openConfirmationModal}
                                                     title={t('main:confirmationModalTitle')}
                                                     message={t('settings:deleteTokenConfirmation')}
                                                     handleYes={manageTokenDeletion}
                                                     handleNo={() => setOpenConfirmationModal(false)}/>}
      </GenericSettingView>

    );

}

export default connector(TokensSettings)
