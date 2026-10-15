import { useTranslations } from '@/i18n/hooks/useTranslations';
import CommonDialog from '@/components/Dialog/CommonDialog';
import { memo } from 'react';

type DeleteDialogProps = {
  deleteDialogOpen: boolean;
  cancelDelete: () => void;
  confirmDelete: () => void;
  title: string;
  description: string;
};

function DeleteDialog({
  deleteDialogOpen,
  cancelDelete,
  confirmDelete,
  title,
  description,
}: DeleteDialogProps) {
  const { t: tCommon } = useTranslations('common');

  return (
    <CommonDialog
      open={deleteDialogOpen}
      onClose={cancelDelete}
      title={title}
      description={description}
      primaryButtonText={tCommon('form.delete')}
      secondaryButtonText={tCommon('form.cancel')}
      onPrimaryAction={confirmDelete}
      onSecondaryAction={cancelDelete}
      primaryButtonColor="error"
      secondaryButtonColor="inherit"
      maxWidth="xs"
      titleColor="#721c24"
    />
  );
}

export default memo(DeleteDialog);
