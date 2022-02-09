// import React, { PropsWithChildren, useState, useEffect } from 'react';
// import Particles from 'react-tsparticles';
// import { IOptions, RecursivePartial } from 'tsparticles';
// import { useTranslation } from 'react-i18next';
// import { Button, TextField, Typography, useTheme } from '@mui/material';
// import { styled } from '@mui/material/styles';
// import CircularProgress from '@material-ui/core/CircularProgress';
// import { ConnectedProps, connect } from 'react-redux';
// import { useForm } from 'react-hook-form';
// import debug from 'debug';
// import { AppState } from '../../../store/reducers';
// import { loginUser, logoutAction } from '../../../store/auth';
// import { login as loginRequest, needAuth, refresh } from '../../../services/api/auth';
// import particleOptions from './particle';
// import logo from '../../../assets/antarestlogo.png';
// import { updateRefreshInterceptor } from '../../../services/api/client';
// import { UserInfo } from '../../../common/types';
// import { reconnectWebsocket } from '../../../store/websockets';

// const logError = debug('antares:loginwrapper:error');

// const Main = styled('div')(({ theme }) => ({
//   flexGrow: 1,
//   display: 'flex',
//   alignItems: 'center',
//   justifyContent: 'center',
//   zIndex: 999,
//   backgroundColor: theme.palette.grey[200],
// }));

// const BackgroundParticle = styled(Particles)(({ theme }) => ({
//   position: 'absolute',
//   width: '100%',
//   height: '100%',
//   boxSizing: 'border-box',
//   overflow: 'hidden',
// }));

// const ErrorMessage = styled('div')(({ theme }) => ({
//   marginTop: theme.spacing(2),
//   color: theme.palette.error.main,
//   marginBottom: -theme.spacing(4),
//   fontSize: '0.9rem',
// }));

// type FormStatus = 'loading' | 'default' | 'success';

// interface Inputs {
//   username: string;
//   password: string;
// }

// const mapState = (state: AppState) => ({
//   user: state.auth.user,
// });

// const mapDispatch = ({
//   login: loginUser,
//   logout: logoutAction,
//   reconnectWs: reconnectWebsocket,
// });

// const connector = connect(mapState, mapDispatch);
// type PropsFromRedux = ConnectedProps<typeof connector>;
// type PropTypes = PropsFromRedux;

// const LoginWrapper = (props: PropsWithChildren<PropTypes>) => {
//   const { register, handleSubmit, reset } = useForm<Inputs>();
//   const [status, setStatus] = useState<FormStatus>('default');
//   const [authRequired, setAuthRequired] = useState<boolean>();
//   const [connexionError, setConnexionError] = useState(false);
//   const [loginError, setLoginError] = useState<string>();
//   const [t] = useTranslation();
//   const theme = useTheme();
//   const { children } = props;
//   const { user, login, logout, reconnectWs } = props;

//   const onSubmit = async (data: Inputs) => {
//     setStatus('loading');
//     setLoginError('');
//     setTimeout(async () => {
//       try {
//         const res = await loginRequest(data.username, data.password);
//         setStatus('success');
//         login(res);
//       } catch (e) {
//         setStatus('default');
//         setLoginError((e as any).data?.message || t('main:loginError'));
//       } finally {
//         reset({ username: data.username });
//       }
//     }, 500);
//   };

//   useEffect(() => {
//     (async () => {
//       try {
//         if (user) {
//           updateRefreshInterceptor(async (): Promise<UserInfo|undefined> => {
//             try {
//               return refresh(user, login, logout);
//             } catch (e) {
//               logError('Failed to refresh token');
//             }
//             return undefined;
//           });
//         }
//         const res = await needAuth();
//         setAuthRequired(res);
//       } catch (e) {
//         setConnexionError(true);
//       }
//     })();
//   }, [user]);

//   useEffect(() => {
//     if (authRequired !== undefined && !authRequired) {
//       reconnectWs();
//     }
//   }, [authRequired]);

//   if (authRequired === undefined) {
//     console.log('Auth required');
//     //return null;
//   }

//   if (connexionError) {
//     console.log('Connexion error');
//     //return null;
//   }

//   if (!authRequired || user) {
//     return <>{children}</>;
//   }

//   return (
//     <div style={{display: 'flex', height: '100%'}}>
//       <div style={{ flex: '40% 0 0', backgroundColor: theme.palette.primary.dark,}}>
//         <div style={{ height: '100%', position: 'relative' }}>
//           <BackgroundParticle
//             id="tsparticles"
//             options={particleOptions as RecursivePartial<IOptions>}
//           />
//           <div style={{ zIndex: 50, position: 'absolute', top: 0, display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', width: '100%' }}>
//             <img style={{ backgroundColor: '#fff' }} height="140px" src={logo} alt="logo" />
//           </div>
//         </div>
//       </div>
//       <Main>
//         <div>
//           <Typography variant="h2" component="h1">Antares Web</Typography>
//           <div style={{ width: '70%'}}>
//             <form style={{ marginTop: theme.spacing(2) }} onSubmit={handleSubmit(onSubmit)}>
//               <TextField
//                 required
//                 id="login"
//                 label="NNI"
//                 fullWidth
//                 {...register('username')}
//                 //inputProps={{ name: 'username', ref: register({ required: true }) }}
//               />
//               <TextField
//                 id="password"
//                 label={t('main:password')}
//                 required
//                 fullWidth
//                 type="password"
//                 //inputProps={{ name: 'password', ref: register({ required: true }) }}
//                 {...register('password')}
//               />
//               {loginError && (
//                 <ErrorMessage>{loginError}</ErrorMessage>
//               )}
//               <div style={{ display: 'flex', justifyContent: 'center', marginTop: theme.spacing(6) }}>
//                 <Button disabled={status === 'loading'} type="submit" variant="contained" color="primary">
//                   {status === 'loading' && <CircularProgress size="1em" style={{ marginRight: '1em' }} />}
//                   {t('main:connexion')}
//                 </Button>
//               </div>
//             </form>
//           </div>
//         </div>
//       </Main>
//     </div>
//   );
// };

// export default connector(LoginWrapper);

export default {};
