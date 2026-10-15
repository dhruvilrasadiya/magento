import React, { memo, useState, useRef, useEffect, Dispatch, SetStateAction } from 'react';

import { Box, TextField, IconButton, Fab, Chip, Switch, FormControlLabel } from '@mui/material';
import SendIcon from '@mui/icons-material/Send';
import { useTranslations } from '@/i18n/hooks/useTranslations';
import { useMediaQuery } from '@mui/material';
import { useTheme } from '@mui/system';
import { ArrowDownward } from '@mui/icons-material';
import { ChatCommandOptions } from './ChatCommandOptions';
import { COMMAND_OPTIONS } from '@/pages/Chat';

type Props = {
  message: string;
  setMessage: (message: string) => void;
  handleSendMessage: () => void;
  handleKeyPress: (e: React.KeyboardEvent) => void;
  isCurrentSessionLoading: boolean;
  sessionLoading: boolean;
  handleScrollToBottomClick: () => void;
  showScrollToBottom: boolean;
  selectedOption: (typeof COMMAND_OPTIONS)[0] | null;
  setSelectedOption: (option: (typeof COMMAND_OPTIONS)[0] | null) => void;
  setIsAutoSendEmail: Dispatch<SetStateAction<boolean>>;
};

function ChatInput({
  message,
  setMessage,
  handleSendMessage,
  handleKeyPress,
  isCurrentSessionLoading,
  sessionLoading,
  handleScrollToBottomClick,
  showScrollToBottom,
  selectedOption,
  setSelectedOption,
  setIsAutoSendEmail,
}: Props) {
  const { t: tChat } = useTranslations('chat');
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));

  const [showOptions, setShowOptions] = useState(false);
  const [filteredOptions, setFilteredOptions] = useState(COMMAND_OPTIONS);
  const [selectedIndex, setSelectedIndex] = useState(0);
  const textFieldRef = useRef<HTMLInputElement>(null);
  const optionsRef = useRef<HTMLDivElement>(null);

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    setMessage(value);

    if (value.endsWith('/')) {
      setShowOptions(true);
      setFilteredOptions(COMMAND_OPTIONS);
      setSelectedIndex(0);
    } else if (showOptions) {
      const lastSlashIndex = value.lastIndexOf('/');
      if (lastSlashIndex !== -1) {
        const searchTerm = value.substring(lastSlashIndex + 1).toLowerCase();
        const filtered = COMMAND_OPTIONS.filter(
          (option) =>
            option.label.toLowerCase().includes(searchTerm) ||
            option.value.toLowerCase().includes(searchTerm)
        );
        setFilteredOptions(filtered);
        setSelectedIndex(0);
      } else {
        setShowOptions(false);
      }
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (showOptions && filteredOptions.length > 0) {
      switch (e.key) {
        case 'ArrowDown':
          e.preventDefault();
          setSelectedIndex((prev) => (prev + 1) % filteredOptions.length);
          break;
        case 'ArrowUp':
          e.preventDefault();
          setSelectedIndex((prev) => (prev - 1 + filteredOptions.length) % filteredOptions.length);
          break;
        case 'Enter':
          e.preventDefault();
          const selectedOption = filteredOptions[selectedIndex];
          selectOption(selectedOption);
          break;
        case 'Escape':
          e.preventDefault();
          setShowOptions(false);
          break;
        default:
          handleKeyPress(e);
      }
    } else {
      handleKeyPress(e);
    }
  };

  const selectOption = (option: (typeof COMMAND_OPTIONS)[0] | null) => {
    setShowOptions(false);
    setSelectedOption(option);
    let updateMessage = message.replace('/', '');

    setMessage(updateMessage);
    setTimeout(() => {
      textFieldRef.current?.focus();
    }, 0);
  };

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (optionsRef.current && !optionsRef.current.contains(event.target as Node)) {
        setShowOptions(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, []);

  return (
    <>
      {showScrollToBottom && (
        <Fab
          size={isMobile ? 'medium' : 'small'}
          color="primary"
          aria-label="scroll to bottom"
          onClick={handleScrollToBottomClick}
          sx={{
            position: 'absolute',
            bottom: isMobile ? 100 : 120,
            right: isMobile ? 16 : 24,
            zIndex: 1000,
            bgcolor: '#1976d2',
            color: 'white',
            opacity: showScrollToBottom ? 1 : 0,
          }}
        >
          <ArrowDownward
            sx={{
              fontSize: isMobile ? 24 : 20,
              transition: 'transform 0.2s ease',
            }}
          />
        </Fab>
      )}

      <Box sx={{ position: 'relative' }}>
        {showOptions && filteredOptions.length > 0 && (
          <ChatCommandOptions
            filteredOptions={filteredOptions}
            selectedIndex={selectedIndex}
            selectOption={selectOption}
            optionsRef={optionsRef}
          />
        )}

        {selectedOption && (
          <Box
            sx={{
              p: 2,
              pb: 1,
              pt: 1,
              borderTop: '1px solid #c0c0c054',
            }}
          >
            <Chip
              icon={selectedOption.icon}
              label={tChat(selectedOption.label)}
              variant="filled"
              color="primary"
              onDelete={() => selectOption(null)}
            />
            {selectedOption.id === 'email' && (
              <FormControlLabel
                control={<Switch onChange={(e) => setIsAutoSendEmail(e.target.checked)} />}
                label={tChat('commandOptions.autosend')}
                labelPlacement="start"
              />
            )}
          </Box>
        )}

        <Box
          component="form"
          sx={{
            p: 2,
            bgcolor: '#f5f7fa',
            display: 'flex',
            alignItems: 'center',
            pt: 0,
          }}
          onSubmit={(e) => {
            e.preventDefault();
            if (!showOptions) {
              handleSendMessage();
            }
          }}
        >
          <TextField
            // multiline
            // minRows={1}
            // maxRows={3}
            ref={textFieldRef}
            autoFocus
            fullWidth
            placeholder={tChat('conversation.typeMessage')}
            variant="outlined"
            size="medium"
            value={message}
            onChange={handleInputChange}
            onKeyDown={handleKeyDown}
            disabled={isCurrentSessionLoading || sessionLoading}
            sx={{
              mr: 1,
              '& .MuiOutlinedInput-root': {
                borderRadius: '24px',
                bgcolor: 'white',
                transition: 'box-shadow 0.2s ease',
                // alignItems: 'flex-start', // for multiline
              },
              '& .MuiOutlinedInput-notchedOutline': {
                border: 'none',
              },
              '& .MuiInputBase-inputMultiline': {
                padding: '8px 16px',
              },
            }}
            slotProps={{
              input: {
                sx: { py: 0.5, px: 2 },
              },
            }} //<--- If Add multiline then remove slotProps.
          />

          <IconButton
            aria-label="send message"
            onClick={handleSendMessage}
            disabled={isCurrentSessionLoading || sessionLoading || !message.trim() || showOptions}
            sx={{
              bgcolor: message.trim() && !showOptions ? '#0d47a1' : '#c9c9c9',
              color: 'white',
              '&:hover': {
                bgcolor: message.trim() && !showOptions ? '#1565c0' : '#c9c9c9',
              },
              width: 48,
              height: 48,
            }}
          >
            <SendIcon />
          </IconButton>
        </Box>
      </Box>
    </>
  );
}

export default memo(ChatInput);
