import React from 'react';
import { Box, Button, ButtonProps, CircularProgress } from '@mui/material';
import { blue } from '@mui/material/colors';

interface OwnProps {
  // eslint-disable-next-line react/no-unused-prop-types
  progressColor?: string;
  fakeDelay?: number;
};

const ButtonLoader = (props: ButtonProps & OwnProps) => {
  const { children, onClick, fakeDelay = 0 } = props;
  const [loading, setLoading] = React.useState(false);

  const handleButtonClick = async (event: React.MouseEvent<HTMLButtonElement, MouseEvent>) => {
    if (!loading && !!onClick) {
      setLoading(true);
      setTimeout(async () => {
        try {
          await onClick(event);
        } finally {
          setLoading(false);
        }
      }, fakeDelay);
    }
  };

  const forwardedProps = { ...props };
  delete forwardedProps.fakeDelay;
  delete forwardedProps.progressColor;

  return (
    <Box sx={{
        m: 1,
        position: 'relative',
        display: 'inline',       
    }}>
      <Button
        // eslint-disable-next-line react/jsx-props-no-spreading
        {...forwardedProps}
        disabled={loading}
        onClick={handleButtonClick}
      >
        {children}
      </Button>
      {loading && <CircularProgress size={24}
                                    sx={{
                                        color: props.progressColor,
                                        position: 'absolute',
                                        top: '50%',
                                        left: '50%',
                                        marginTop: -12,
                                        marginLeft: -12,
                                    }} />}
    </Box>
  );
};

ButtonLoader.defaultProps = {
  progressColor: blue[400],
  fakeDelay: 0,
};

export default ButtonLoader;
