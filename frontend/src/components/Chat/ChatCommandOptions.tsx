import { useTranslations } from '@/i18n/hooks/useTranslations';
import { Box, Paper, List, ListItemText, ListItemButton } from '@mui/material';
import { JSX } from 'react';

type Props = {
  filteredOptions: { id: string; icon: JSX.Element; label: string; value: string }[];
  selectedIndex: number;
  selectOption: (option: { id: string; icon: JSX.Element; label: string; value: string }) => void;
  optionsRef: React.RefObject<HTMLDivElement | null>;
};

export const ChatCommandOptions = ({
  filteredOptions,
  selectedIndex,
  selectOption,
  optionsRef,
}: Props) => {
  const { t: tChat } = useTranslations('chat');

  return (
    <Paper
      ref={optionsRef}
      elevation={0}
      sx={{
        position: 'absolute',
        bottom: '100%',
        left: 16,
        width: 150,
        maxHeight: 200,
        overflowY: 'auto',
        zIndex: 1500,
        borderRadius: 2,
        mb: 0.5,
        bgcolor: 'white',
        border: '1px solid rgb(255, 255, 255)',
      }}
    >
      <List sx={{ py: 0 }}>
        {filteredOptions.map((option, index) => (
          <ListItemButton
            key={option.id}
            selected={index === selectedIndex}
            onClick={() => selectOption(option)}
            sx={{
              cursor: 'pointer',
              px: 1,
              py: 0.5,
              minHeight: 'auto',
              '&:hover': {
                bgcolor: '#f0f0f0',
              },
              transition: 'background-color 0.15s ease',
            }}
          >
            <ListItemText
              primary={
                <Box sx={{ display: 'flex', alignItems: 'center' }}>
                  {option.icon}
                  {tChat(option.label)}
                </Box>
              }
              slotProps={{
                primary: {
                  fontSize: 12,
                  fontWeight: 500,
                  color: 'text.primary',
                  noWrap: true,
                },
              }}
            />
          </ListItemButton>
        ))}
      </List>
    </Paper>
  );
};
