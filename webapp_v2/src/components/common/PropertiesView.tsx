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

const StyledAddButton = styled(AddIcon)(({ theme }) => ({
  position: 'absolute',
  left: '20px',
  bottom: '25px',
  cursor: 'pointer',
  borderRadius: '50px',
  padding: '16px',
  backgroundColor: theme.palette.primary.main,
  color: 'white',
  '&:hover': {
    backgroundColor: theme.palette.primary.dark,
  },
  height: '25px',
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
        sx={{ margin: '16px' }}
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
      <StyledAddButton onClick={onAdd} />
    </Box>
  );
}

export default PropertiesView;
