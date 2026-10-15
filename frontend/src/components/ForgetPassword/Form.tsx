import { Box, Button, TextField, Typography } from '@mui/material';
import { Dispatch, SetStateAction, useCallback, useState } from 'react';
import { useForm, Controller } from 'react-hook-form';
import Grid from '@mui/material/Grid';
import SideImage from '@/assets/images/login_1.png';
import { ArrowBackIos } from '@mui/icons-material';
import { ForgetPasswordType, FormType } from '@/types/types';
import { forgetPassword } from '@/services/api';
import { enqueueSnackbar } from 'notistack';
import debounce from 'lodash.debounce';
import { useTranslations } from '@/i18n/hooks/useTranslations';

type Props = {
  setFormType: Dispatch<SetStateAction<FormType>>;
};

export default function ForgetPasswordForm({ setFormType }: Props) {
  const {
    control,
    handleSubmit,
    formState: { errors, isValid },
    trigger,
  } = useForm<ForgetPasswordType>({
    defaultValues: {
      email: '',
    },
  });
  const [submissionAttempted, setSubmissionAttempted] = useState<boolean>(false);
  const [loading, setLoading] = useState<boolean>(false);
  const { t: tAuth } = useTranslations('auth');
  const { t: tCommon } = useTranslations('common');

  const debouncedSubmit = useCallback(
    debounce(async (data: ForgetPasswordType) => {
      if (loading) return;

      try {
        setLoading(true);
        const result = await forgetPassword(data);
        if (result) {
          enqueueSnackbar(tAuth('success.resetPasswordLinkSent'), {
            variant: 'success',
          });
        }
      } catch (error: any) {
        const errorMessage =
          error.response?.data?.detail === '404: Email not registered'
            ? 'errors.emailNotRegistered'
            : 'errors.resetPasswordError';
        enqueueSnackbar(tAuth(errorMessage), { variant: 'error' });
        console.error('Password reset error:', error);
      } finally {
        setLoading(false);
      }
    }, 500),
    [loading]
  );

  const onSubmit = async (data: ForgetPasswordType) => {
    setSubmissionAttempted(true);
    debouncedSubmit(data);
  };

  return (
    <Grid container sx={{ minHeight: '100vh' }} justifyContent={'space-between'}>
      {/* Left Section - Form */}
      <Grid
        size={{ xs: 12, md: 6 }}
        sx={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          bgcolor: '#fff',
          mb: 10,
        }}
      >
        <Box
          maxWidth={400}
          mx="auto"
          mt={8}
          p={4}
          borderRadius={2}
          bgcolor="white"
          border={1}
          borderColor={'lightgray'}
        >
          <Button
            variant="text"
            color="inherit"
            startIcon={<ArrowBackIos style={{ fontSize: 13 }} />}
            disableRipple={true}
            onClick={() => setFormType('Login')}
          >
            {tAuth('forgotPassword.backToLogin')}
          </Button>
          <Typography variant="h5" fontWeight={700} gutterBottom>
            {tAuth('forgotPassword.title')}
          </Typography>
          <Typography color="text.secondary" mb={3}>
            {tAuth('forgotPassword.description')}
          </Typography>

          <form onSubmit={handleSubmit(onSubmit)} noValidate>
            <Controller
              name="email"
              control={control}
              rules={{
                required: tAuth('validation.emailRequired'),
                pattern: {
                  value: /^\S+@\S+$/i,
                  message: tAuth('validation.invalidEmail'),
                },
              }}
              render={({ field }) => (
                <TextField
                  label={tCommon('form.email')}
                  fullWidth
                  margin="normal"
                  {...field}
                  error={!!errors.email}
                  helperText={errors.email?.message}
                  onChange={(e) => {
                    field.onChange(e);
                    if (submissionAttempted) {
                      trigger('email');
                    }
                  }}
                />
              )}
            />

            <Button
              type="submit"
              fullWidth
              variant="contained"
              sx={{
                mt: 3,
                backgroundColor: '#0047AB',
                fontWeight: 'bold',
                py: 1.2,
              }}
              loading={loading}
              disabled={loading || (submissionAttempted && !isValid)}
            >
              {tCommon('form.submit')}
            </Button>
          </form>
        </Box>
      </Grid>
      {/* Right Section - Image */}
      <Grid
        size={{ xs: 0, md: 6 }}
        sx={{
          backgroundImage: `url(${SideImage})`,
          backgroundSize: 'contain',
          backgroundPosition: 'center',
          backgroundRepeat: 'no-repeat',
        }}
      />
    </Grid>
  );
}
