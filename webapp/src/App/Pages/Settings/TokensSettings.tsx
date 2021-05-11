import React, {useEffect} from 'react';
import { connect, ConnectedProps } from 'react-redux';
import { useSnackbar } from 'notistack';
import { useTranslation } from 'react-i18next';
import { AppState } from '../../reducers';
import GenericSettingView from '../../../components/Settings/GenericSettingView'
//import ItemSettings from '../../../components/Settings/ItemSettings'

const mapState = (state: AppState) => ({
    user: state.auth.user,
  });

const connector = connect(mapState);
type ReduxProps = ConnectedProps<typeof connector>;
type PropTypes = ReduxProps;

const TokensSettings = (props: PropTypes) => {

    const [t] = useTranslation();
    const { enqueueSnackbar } = useSnackbar();
    const {user} = props;

    useEffect(() => {
      const init = () =>{
        enqueueSnackbar(t('settings:tokensError'), { variant: 'error' });
      }
      init();
    }, [user, t, enqueueSnackbar]);

    return (
      <GenericSettingView searchFilter={(input: string) => console.log(`Search string is ${input}`)}
                          placeholder={t('settings:tokensSearchbarPlaceholder')}
                          buttonValue={t('settings:createToken')}
                          onButtonClick={() => console.log("Button")}>

      </GenericSettingView>
    );

}

export default connector(TokensSettings)
