import {
  Box,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  TextField,
  Typography,
  Divider,
  Autocomplete,
  Chip,
} from '@mui/material';
import { Send, Close, Email } from '@mui/icons-material';
import { memo, useState, useEffect } from 'react';
import { EmailData } from '@/types/types';
import { useTranslations } from '@/i18n/hooks/useTranslations';

type Props = {
  emailModalOpen: boolean;
  handleEmailClose: () => void;
  emailData: EmailData;
  handleEmailFieldChange: (field: string, value: string[] | string) => void;
  handleSendEmail: () => void;
  emailSuggestions?: string[];
  isSendMailLoading: boolean;
};

const EMAIL_REGEX = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

// const DEFAULT_EMAIL_SUGGESTIONS = [
//   'john.doe@example.com',
//   'jane.smith@company.com',
//   'support@helpdesk.com',
//   'admin@organization.org',
//   'info@business.net',
// ];

const EmailDialog = ({
  emailModalOpen,
  handleEmailClose,
  emailData,
  handleEmailFieldChange,
  handleSendEmail,
  emailSuggestions = [],
  isSendMailLoading,
}: Props) => {
  const [toEmails, setToEmails] = useState<string[]>([]);
  const [ccEmails, setCcEmails] = useState<string[]>([]);
  const [bccEmails, setBccEmails] = useState<string[]>([]);

  const { t: tChat } = useTranslations('chat');
  const isDisabled = emailData.isAlreadySent || isSendMailLoading;

  useEffect(() => {
    if (emailModalOpen) {
      setToEmails(emailData.to ? emailData.to.map((email) => email.trim()).filter(Boolean) : []);
      setCcEmails(emailData.cc ? emailData.cc.map((email) => email.trim()).filter(Boolean) : []);
      setBccEmails(emailData.bcc ? emailData.bcc.map((email) => email.trim()).filter(Boolean) : []);
    }
  }, [emailModalOpen, emailData.to, emailData.cc, emailData.bcc]);

  const isValidEmail = (email: string): boolean => {
    return EMAIL_REGEX.test(email.trim());
  };

  const handleToChange = (_event: any, newValue: string[]) => {
    setToEmails(newValue);
    handleEmailFieldChange('to', newValue);
  };

  const handleCcChange = (_event: any, newValue: string[]) => {
    setCcEmails(newValue);
    handleEmailFieldChange('cc', newValue);
  };

  const handleBccChange = (_event: any, newValue: string[]) => {
    setBccEmails(newValue);
    handleEmailFieldChange('bcc', newValue);
  };

  const getFilteredOptions = (options: string[], inputValue: string) => {
    const filtered = options.filter((option) =>
      option.toLowerCase().includes(inputValue.toLowerCase())
    );

    if (inputValue && isValidEmail(inputValue) && !filtered.includes(inputValue)) {
      filtered.push(inputValue);
    }

    return filtered;
  };

  const canSend =
    toEmails.length > 0 &&
    toEmails.every((email) => isValidEmail(email)) &&
    emailData.message?.trim().length > 0;

  return (
    <Dialog
      open={emailModalOpen}
      onClose={handleEmailClose}
      maxWidth="md"
      fullWidth
      slotProps={{
        paper: {
          sx: {
            borderRadius: 3,
            maxHeight: '85vh',
          },
        },
      }}
    >
      <DialogTitle
        sx={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          pb: 1,
        }}
      >
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <Email color="primary" />
          <Typography variant="h6" component="div">
            {tChat('emailDialog.title')}
          </Typography>
        </Box>
        <IconButton
          onClick={handleEmailClose}
          size="small"
          sx={{
            color: 'text.secondary',
            '&:hover': { bgcolor: 'action.hover' },
          }}
        >
          <Close />
        </IconButton>
      </DialogTitle>

      <DialogContent sx={{ px: 3 }}>
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2.5, mt: 1 }}>
          {/* To Field with Autocomplete */}
          <Autocomplete
            multiple
            freeSolo
            options={emailSuggestions}
            value={toEmails}
            onChange={handleToChange}
            filterOptions={(options, { inputValue }) => getFilteredOptions(options, inputValue)}
            renderValue={(value, getTagProps) =>
              value.map((option, index) => {
                const { key, ...tagProps } = getTagProps({ index });
                return (
                  <Chip
                    key={key}
                    label={option}
                    {...tagProps}
                    color={isValidEmail(option) ? 'primary' : 'error'}
                    variant="outlined"
                    size="small"
                  />
                );
              })
            }
            renderInput={(params) => (
              <TextField
                {...params}
                label={tChat('emailDialog.form.to.label')}
                placeholder={tChat('emailDialog.form.to.placeholder')}
                variant="outlined"
                size="small"
              />
            )}
            sx={{
              '& .MuiOutlinedInput-root': {
                minHeight: '48px',
                alignItems: 'flex-start',
                pt: 1,
              },
            }}
            disabled={isDisabled}
          />

          {/* CC Field with Autocomplete */}
          <Autocomplete
            multiple
            freeSolo
            options={emailSuggestions}
            value={ccEmails}
            onChange={handleCcChange}
            filterOptions={(options, { inputValue }) => getFilteredOptions(options, inputValue)}
            renderValue={(value, getTagProps) =>
              value.map((option, index) => {
                const { key, ...tagProps } = getTagProps({ index });
                return (
                  <Chip
                    key={key}
                    label={option}
                    {...tagProps}
                    color={isValidEmail(option) ? 'secondary' : 'error'}
                    variant="outlined"
                    size="small"
                  />
                );
              })
            }
            renderInput={(params) => (
              <TextField
                {...params}
                label={tChat('emailDialog.form.cc.label')}
                placeholder={tChat('emailDialog.form.cc.placeholder')}
                variant="outlined"
                size="small"
              />
            )}
            sx={{
              '& .MuiOutlinedInput-root': {
                minHeight: '48px',
                alignItems: 'flex-start',
                pt: 1,
              },
            }}
            disabled={isDisabled}
          />

          {/* BCC Field with Autocomplete */}
          <Autocomplete
            multiple
            freeSolo
            options={emailSuggestions}
            value={bccEmails}
            onChange={handleBccChange}
            filterOptions={(options, { inputValue }) => getFilteredOptions(options, inputValue)}
            renderValue={(value, getTagProps) =>
              value.map((option, index) => {
                const { key, ...tagProps } = getTagProps({ index });
                return (
                  <Chip
                    key={key}
                    label={option}
                    {...tagProps}
                    color={isValidEmail(option) ? 'secondary' : 'error'}
                    variant="outlined"
                    size="small"
                  />
                );
              })
            }
            renderInput={(params) => (
              <TextField
                {...params}
                label={tChat('emailDialog.form.bcc.label')}
                placeholder={tChat('emailDialog.form.bcc.placeholder')}
                variant="outlined"
                size="small"
              />
            )}
            sx={{
              '& .MuiOutlinedInput-root': {
                minHeight: '48px',
                alignItems: 'flex-start',
                pt: 1,
              },
            }}
            disabled={isDisabled}
          />

          {/* Subject Field */}
          <TextField
            label={tChat('emailDialog.form.subject.label')}
            variant="outlined"
            fullWidth
            value={emailData.subject || ''}
            onChange={(e) => handleEmailFieldChange('subject', e.target.value)}
            placeholder={tChat('emailDialog.form.subject.placeholder')}
            size="small"
            sx={{
              '& .MuiOutlinedInput-root': {
                transition: 'all 0.2s ease-in-out',
              },
            }}
            disabled={isDisabled}
          />

          <Divider />

          {/* Message Preview Label */}
          <Typography variant="subtitle2" color="text.secondary" sx={{ mb: -1 }}>
            {tChat('emailDialog.form.preview')}
          </Typography>

          {/* Message Field */}
          <TextField
            label={tChat('emailDialog.form.message.label')}
            variant="outlined"
            fullWidth
            multiline
            rows={5}
            value={emailData.message || ''}
            onChange={(e) => handleEmailFieldChange('message', e.target.value)}
            placeholder={tChat('emailDialog.form.message.placeholder')}
            size="small"
            sx={{
              '& .MuiOutlinedInput-root': {
                alignItems: 'flex-start',
                transition: 'all 0.2s ease-in-out',
              },
              '& .MuiOutlinedInput-input': {
                resize: 'vertical',
              },
            }}
            disabled={isDisabled}
          />
        </Box>
      </DialogContent>

      <DialogActions sx={{ px: 3, pb: 2.5, pt: 1.5, gap: 1 }}>
        <Button
          onClick={handleEmailClose}
          color="inherit"
          variant="outlined"
          sx={{ minWidth: 100 }}
          disabled={isDisabled}
        >
          {tChat('emailDialog.form.cancel')}
        </Button>
        <Button
          onClick={handleSendEmail}
          color="primary"
          variant="contained"
          startIcon={<Send />}
          disabled={!canSend || isDisabled}
          loading={isSendMailLoading}
          sx={{
            minWidth: 120,
            '&:disabled': {
              opacity: 0.6,
            },
          }}
        >
          {tChat('emailDialog.form.send')}
        </Button>
      </DialogActions>
    </Dialog>
  );
};

EmailDialog.displayName = 'EmailDialog';

export default memo(EmailDialog);
