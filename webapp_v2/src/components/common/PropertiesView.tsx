import React, { ReactNode } from 'react';
import {
  TextField,
  InputAdornment,
  Box,
  styled,
} from '@mui/material';
import SearchIcon from '@mui/icons-material/Search';
import { useTranslation } from 'react-i18next';
import AddIcon from '@mui/icons-material/Add';

const StyledAddIcon = styled(AddIcon)(({ theme }) => ({
  cursor: 'pointer',
  color: 'black',
  width: '40px',
  height: '40px',
  position: 'absolute',
  left: '5%',
  bottom: '25px',
  borderRadius: '30px',
  padding: '8px',
  backgroundColor: theme.palette.primary.main,
  '&:hover': {
    backgroundColor: theme.palette.primary.dark,
  },
}));

interface PropsType {
    mainContent: ReactNode | undefined;
    secondaryContent: ReactNode;
    onSearchFilterChange: (value: string) => void;
    onAdd: () => void;
}

function PropertiesView(props: PropsType) {
  const { onAdd, onSearchFilterChange, mainContent, secondaryContent } = props;
  const [t] = useTranslation();

  return (
    <Box width="100%" height="100%" display="flex" flexDirection="column" justifyContent="flex-start" alignItems="center" boxSizing="border-box">
      <TextField
        label={t('main:search')}
        variant="outlined"
        InputProps={{
          startAdornment: (
            <InputAdornment position="start">
              <SearchIcon />
            </InputAdornment>
          ),
        }}
        onChange={(e) => onSearchFilterChange(e.target.value as string)}
      />
      {mainContent}
      {secondaryContent}
      <StyledAddIcon onClick={onAdd} />
    </Box>
  );
}

export default PropertiesView;
