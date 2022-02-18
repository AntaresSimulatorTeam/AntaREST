import React from 'react';
import { TextField, SxProps, Theme } from '@mui/material';

interface Props {
    label: string;
    value: string;
    onChange: (value: string) => void;
    sx?: SxProps<Theme> | undefined;
}
const FilledTextInput = (props: Props) => {
    const { label, value, onChange, sx } = props;
  return (
      <TextField label={label} 
                 value={value}
                 onChange={(e: React.ChangeEvent<HTMLTextAreaElement | HTMLInputElement>) => onChange(e.target.value as string)}
                 variant="filled"
                 sx={{
                    ...sx, 
                    background: 'rgba(255, 255, 255, 0.09)',
                    borderRadius: '4px 4px 0px 0px',
                    borderBottom: '1px solid rgba(255, 255, 255, 0.42)',
                  }} />
  );
}

FilledTextInput.defaultProps = {
    sx: undefined,
}

export default FilledTextInput;
