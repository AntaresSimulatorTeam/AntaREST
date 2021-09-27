import React from 'react';
import { createStyles, makeStyles, Theme } from '@material-ui/core/styles';
import CircularProgress from '@material-ui/core/CircularProgress';
import { blue } from '@material-ui/core/colors';
import Button, { ButtonProps } from '@material-ui/core/Button';

interface OwnProps {
  // eslint-disable-next-line react/no-unused-prop-types
  progressColor?: string;
}

const useStyles = makeStyles<Theme, OwnProps>((theme: Theme) =>
  createStyles({
    root: {
      display: 'flex',
      alignItems: 'center',
    },
    wrapper: {
      margin: theme.spacing(1),
      position: 'relative',
      display: 'inline',
    },
    buttonProgress: {
      color: (props) => props.progressColor,
      position: 'absolute',
      top: '50%',
      left: '50%',
      marginTop: -12,
      marginLeft: -12,
    },
  }));

const ButtonLoader = (props: ButtonProps & OwnProps) => {
  const classes = useStyles(props);
  const { children, onClick } = props;
  const [loading, setLoading] = React.useState(false);

  const handleButtonClick = async (event: React.MouseEvent<HTMLButtonElement, MouseEvent>) => {
    if (!loading && !!onClick) {
      setLoading(true);
      try {
        await onClick(event);
      } finally {
        setLoading(false);
      }
    }
  };

  return (
    <div className={classes.wrapper}>
      <Button
        // eslint-disable-next-line react/jsx-props-no-spreading
        {...props}
        disabled={loading}
        onClick={handleButtonClick}
      >
        {children}
      </Button>
      {loading && <CircularProgress size={24} className={classes.buttonProgress} />}
    </div>
  );
};

ButtonLoader.defaultProps = {
  progressColor: blue[400],
};

export default ButtonLoader;
