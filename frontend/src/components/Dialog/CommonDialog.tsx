import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogContentText,
  DialogActions,
  Button,
  IconButton,
  Typography,
  Box,
  SxProps,
  Theme,
} from '@mui/material';
import { Close as CloseIcon } from '@mui/icons-material';
import { memo, ReactNode } from 'react';

type CommonDialogProps = {
  open: boolean;
  onClose: () => void;
  title: string;
  description?: string | ReactNode;
  content?: ReactNode;
  actions?: ReactNode;
  primaryButtonText?: string;
  secondaryButtonText?: string;
  onPrimaryAction?: () => void;
  onSecondaryAction?: () => void;
  primaryButtonColor?: 'primary' | 'secondary' | 'error' | 'info' | 'success' | 'warning';
  secondaryButtonColor?:
    | 'primary'
    | 'secondary'
    | 'error'
    | 'info'
    | 'success'
    | 'warning'
    | 'inherit';
  maxWidth?: 'xs' | 'sm' | 'md' | 'lg' | 'xl' | false;
  fullWidth?: boolean;
  showCloseButton?: boolean;
  titleBackgroundColor?: string;
  titleColor?: string;
  primaryButtonVariant?: 'text' | 'outlined' | 'contained';
  secondaryButtonVariant?: 'text' | 'outlined' | 'contained';
  paperSx?: SxProps<Theme>;
};

function CommonDialog({
  open,
  onClose,
  title,
  description,
  content,
  actions,
  primaryButtonText,
  secondaryButtonText,
  onPrimaryAction,
  onSecondaryAction,
  primaryButtonColor = 'primary',
  secondaryButtonColor = 'inherit',
  maxWidth = 'sm',
  fullWidth = true,
  showCloseButton = true,
  titleBackgroundColor,
  titleColor,
  primaryButtonVariant = 'contained',
  secondaryButtonVariant = 'outlined',
  paperSx,
}: CommonDialogProps) {
  const useDefaultActions = !actions && (onPrimaryAction || onSecondaryAction);

  const handleKeyDown = (event: React.KeyboardEvent) => {
    if (event.key === 'Enter' && onPrimaryAction) {
      event.preventDefault();
      onPrimaryAction();
    }
  };

  return (
    <Dialog
      open={open}
      onClose={onClose}
      maxWidth={maxWidth}
      fullWidth={fullWidth}
      slotProps={{
        paper: {
          sx: {
            borderRadius: 2,
            overflow: 'hidden',
            ...paperSx,
          },
        },
      }}
      aria-labelledby="common-dialog-title"
      onKeyDown={handleKeyDown}
    >
      {/* Dialog Title */}
      <DialogTitle
        id="common-dialog-title"
        component="div"
        sx={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          backgroundColor: titleBackgroundColor,
          color: titleColor,
          p: titleBackgroundColor ? 1.5 : undefined,
        }}
      >
        <Typography variant="h6" sx={{ fontWeight: 500 }}>
          {title}
        </Typography>

        {showCloseButton && (
          <IconButton edge="end" color="inherit" onClick={onClose} aria-label="close" size="small">
            <CloseIcon />
          </IconButton>
        )}
      </DialogTitle>

      {/* Dialog Content */}
      <DialogContent sx={{ pt: description ? 2 : 3, pb: useDefaultActions ? 1 : 2 }}>
        {description && (
          <DialogContentText id="common-dialog-description" sx={{ mb: 2 }}>
            {description}
          </DialogContentText>
        )}

        {content}
      </DialogContent>

      {/* Dialog Actions */}
      {useDefaultActions && (
        <DialogActions sx={{ px: 3, pb: 2, pt: 1 }}>
          {secondaryButtonText && onSecondaryAction && (
            <Button
              onClick={onSecondaryAction}
              color={secondaryButtonColor}
              variant={secondaryButtonVariant}
              sx={{
                borderRadius: 1.5,
                textTransform: 'none',
                px: 2,
                mr: 1,
              }}
            >
              {secondaryButtonText}
            </Button>
          )}

          {primaryButtonText && onPrimaryAction && (
            <Button
              onClick={onPrimaryAction}
              color={primaryButtonColor}
              variant={primaryButtonVariant}
              autoFocus
              sx={{
                borderRadius: 1.5,
                textTransform: 'none',
                px: 2,
              }}
            >
              {primaryButtonText}
            </Button>
          )}
        </DialogActions>
      )}

      {actions && (
        <Box
          sx={{
            px: 3,
            pb: 2,
            pt: 1,
            display: 'flex',
            justifyContent: 'flex-end',
          }}
        >
          {actions}
        </Box>
      )}
    </Dialog>
  );
}

export default memo(CommonDialog);
