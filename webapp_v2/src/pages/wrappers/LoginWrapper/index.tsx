/* eslint-disable react-hooks/exhaustive-deps */
import React, { PropsWithChildren, useState, useEffect } from 'react';
import { Box, Button, CircularProgress, styled, TextField, Typography } from '@mui/material';
import Particles from 'react-tsparticles';
import { IOptions, RecursivePartial } from 'tsparticles';
import { useTranslation } from 'react-i18next';
import { ConnectedProps, connect } from 'react-redux';
import { useForm } from 'react-hook-form';
import debug from 'debug';
import { AppState } from '../../../store/reducers';
import { loginUser, logoutAction } from '../../../store/auth';
import { login as loginRequest, needAuth, refresh } from '../../../services/api/auth';
import particleOptions from './particle';
import logo from './antarestlogo.png';
import GlobalPageLoadingError from '../../../components/common/loaders/GlobalPageLoadingError';
import AppLoader from '../../../components/common/loaders/AppLoader';
import { updateRefreshInterceptor } from '../../../services/api/client';
import { UserInfo } from '../../../common/types';
import { reconnectWebsocket } from '../../../store/websockets';

const logError = debug('antares:loginwrapper:error');

const StyledParticles = styled(Particles)(({ theme }) => ({
  position: 'absolute',
  width: '100%',
  height: '100%',
  boxSizing: 'border-box',
  overflow: 'hidden',
}));

type FormStatus = 'loading' | 'default' | 'success';

interface Inputs {
  username: string;
  password: string;
}

const mapState = (state: AppState) => ({
  user: state.auth.user,
});

const mapDispatch = ({
  login: loginUser,
  logout: logoutAction,
  reconnectWs: reconnectWebsocket,
});

const connector = connect(mapState, mapDispatch);
type PropsFromRedux = ConnectedProps<typeof connector>;
type PropTypes = PropsFromRedux;

function LoginWrapper(props: PropsWithChildren<PropTypes>) {
  const { register, handleSubmit, reset } = useForm<Inputs>();
  const [status, setStatus] = useState<FormStatus>('default');
  const [authRequired, setAuthRequired] = useState<boolean>();
  const [connexionError, setConnexionError] = useState(false);
  const [loginError, setLoginError] = useState<string>();
  const [t] = useTranslation();
  const { children } = props;
  const { user, login, logout, reconnectWs } = props;

  const onSubmit = async (data: Inputs) => {
    setStatus('loading');
    setLoginError('');
    setTimeout(async () => {
      try {
        const res = await loginRequest(data.username, data.password);
        setStatus('success');
        login(res);
      } catch (e) {
        setStatus('default');
        setLoginError((e as any).data?.message || t('main:loginError'));
      } finally {
        reset({ username: data.username });
      }
    }, 500);
  };

  useEffect(() => {
    (async () => {
      try {
        if (user) {
          updateRefreshInterceptor(async (): Promise<UserInfo|undefined> => {
            try {
              return refresh(user, login, logout);
            } catch (e) {
              logError('Failed to refresh token');
            }
            return undefined;
          });
        }
        const res = await needAuth();
        setAuthRequired(res);
      } catch (e) {
        setConnexionError(true);
      }
    })();
  }, [user]);

  useEffect(() => {
    if (authRequired !== undefined && !authRequired) {
      reconnectWs();
    }
  }, [authRequired]);

  if (authRequired === undefined) {
    return <AppLoader />;
  }

  if (connexionError) {
    return <GlobalPageLoadingError />;
  }

  if (!authRequired || user) {
    // eslint-disable-next-line react/jsx-no-useless-fragment
    return <>{children}</>;
  }

  return (
    <Box display="flex" height="100vh">
      <Box flex="40% 0 0" bgcolor="outlineBorder">
        <Box sx={{ height: '100%', position: 'relative' }}>
          <StyledParticles
            id="tsparticles"
            options={particleOptions as RecursivePartial<IOptions>}
          />
          <Box sx={{ zIndex: 50, position: 'absolute', top: 0, display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', width: '100%' }}>
            <img style={{ backgroundColor: '#fff' }} height="140px" src={logo} alt="logo" />
          </Box>
        </Box>
      </Box>
      <Box
        flexGrow={1}
        display="flex"
        alignItems="center"
        justifyContent="center"
        zIndex={999}
        bgcolor="grey.200"
      >
        <Box>
          <Typography variant="h2" component="h1">Antares Web</Typography>
          <Box width="70%">
            <form style={{ marginTop: '16px' }} onSubmit={handleSubmit(onSubmit)}>
              <TextField
                required
                id="login"
                label="NNI"
                fullWidth
                sx={{ my: 2 }}
                inputProps={{ ...register('username', { required: true }) }}
              />
              <TextField
                id="password"
                label={t('main:password')}
                required
                fullWidth
                type="password"
                inputProps={{ ...register('password', { required: true }) }}
              />
              {loginError && (
                <Box mt={2} color="error.main" mb={4} sx={{ fontSize: '0.9rem' }}>{loginError}</Box>
              )}
              <Box display="flex" justifyContent="center" mt={6}>
                <Button disabled={status === 'loading'} type="submit" variant="contained" color="primary">
                  {status === 'loading' && <CircularProgress size="1em" sx={{ mr: '1em' }} />}
                  {t('main:connexion')}
                </Button>
              </Box>
            </form>
          </Box>
        </Box>
      </Box>
    </Box>
  );
}

export default connector(LoginWrapper);
