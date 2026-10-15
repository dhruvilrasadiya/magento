import { memo, useEffect, useState } from 'react';
import { TextField, Box, Typography } from '@mui/material';
import CommonDialog from '@/components/Dialog/CommonDialog';
import { useTranslations } from '@/i18n/hooks/useTranslations';

function EditTitleDialog({
  open,
  onClose,
  initialTitle,
  onSave,
}: {
  open: boolean;
  onClose: () => void;
  initialTitle: string;
  onSave: (newTitle: string) => void;
}) {
  const [title, setTitle] = useState('');
  const [error, setError] = useState('');
  const { t: tChat } = useTranslations('chat');
  const { t: tCommon } = useTranslations('common');

  useEffect(() => {
    setTitle(initialTitle || tChat('session.edit.title.label'));
  }, [initialTitle, tChat]);

  const handleTitleChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const value = event.target.value;
    setTitle(value);

    if (!value || value.trim() === '') {
      setError(tChat('session.edit.title.validation.empty'));
    } else if (value.length > 50) {
      setError(tChat('session.edit.title.validation.tooLong'));
    } else {
      setError('');
    }
  };

  const handleSave = () => {
    if (!error && title?.trim()) {
      onSave(title?.trim());
    }
  };

  return (
    <CommonDialog
      open={open}
      onClose={onClose}
      title={tChat('session.edit.title.label')}
      titleColor="#0d47a1"
      primaryButtonText={tCommon('form.save')}
      secondaryButtonText={tCommon('form.cancel')}
      onPrimaryAction={handleSave}
      onSecondaryAction={onClose}
      primaryButtonColor="primary"
      content={
        <Box sx={{ mb: 1 }}>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
            {tChat('session.edit.title.instruction')}
          </Typography>
          <TextField
            autoFocus
            fullWidth
            label={tChat('session.edit.title.label')}
            variant="outlined"
            value={title}
            onChange={handleTitleChange}
            error={!!error}
            helperText={error || ' '}
            slotProps={{
              input: { sx: { borderRadius: 1.5 } },
            }}
            placeholder={tChat('session.edit.title.placeholder')}
          />
        </Box>
      }
    />
  );
}

export default memo(EditTitleDialog);
