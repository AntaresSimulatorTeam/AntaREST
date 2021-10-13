import { AxiosError } from 'axios';
import { OptionsObject, SnackbarKey, SnackbarMessage } from 'notistack';
import React from 'react';
import SnackErrorMessage from './SnackErrorMessage';

export type SnackbarDetails = {
  status: string;
  description: string;
  exception: string;
};

const enqueueErrorSnackbar = (enqueueSnackbar: (message: SnackbarMessage, options?: OptionsObject | undefined) => SnackbarKey, message: string, details: AxiosError) => enqueueSnackbar(message, { variant: 'error',
  content: (key, msg) => (
    <SnackErrorMessage id={key} message={msg} details={details} />
  ) });

export default enqueueErrorSnackbar;
