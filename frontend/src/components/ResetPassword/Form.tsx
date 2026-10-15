import { Box, Button, IconButton, InputAdornment, TextField, Typography } from '@mui/material';
import { Visibility, VisibilityOff } from '@mui/icons-material';
import { Dispatch, SetStateAction, useState } from 'react';
import { useForm, Controller } from 'react-hook-form';
import Grid from '@mui/material/Grid';
import SideImage from '@/assets/images/login_1.png';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { FormType, ResetPasswordPayload, ResetPasswordType } from '@/types/types';
import { resetPassword } from '@/services/api';
import { enqueueSnackbar } from 'notistack';
import { useTranslations } from '@/i18n/hooks/useTranslations';
import { routes } from '@/constants/routes';

type Props = {
  setFormType: Dispatch<SetStateAction<FormType>>;
};

export default function ResetPasswordForm({ setFormType }: Props) {
  const {
    control,
    handleSubmit,
    watch,
    formState: { errors },
  } = useForm<ResetPasswordType>({
    defaultValues: {
      password: '',
      confirmPassword: '',
    },
  });

  const [showPassword, setShowPassword] = useState<boolean>(false);
  const [showConfirmPassword, setConfirmShowPassword] = useState<boolean>(false);
  const [loading, setLoading] = useState<boolean>(false);
  const [searchParams] = useSearchParams();
  const password = watch('password');
  const token = searchParams.get('token');
  const navigate = useNavigate();
  const { t: tAuth } = useTranslations('auth');

  const onSubmit = async (data: ResetPasswordType) => {
    try {
      setLoading(true);
      const payload: ResetPasswordPayload = {
        new_password: data.password,
        token: token!,
      };
      const result = await resetPassword(payload);
      if (result && result.status === 200) {
        navigate(routes.login);
        setFormType('Login');
        enqueueSnackbar(tAuth('resetPassword.success'), { variant: 'success' });
      }
      setLoading(false);
    } catch (error: any) {
      setLoading(false);
      const errorMessage =
        error.response?.data?.detail === 'Invalid or expired token'
          ? 'errors.invalidToken'
          : 'errors.resetPasswordError';
      enqueueSnackbar(`${tAuth(errorMessage)}`, { variant: 'error' });
      console.log(error);
    }
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
          <Typography variant="h4" fontWeight={700} gutterBottom>
            {tAuth('resetPassword.title')}
          </Typography>
          <Typography color="text.secondary" mb={3}>
            {tAuth('resetPassword.newPasswordInstructions')}
          </Typography>

          <form onSubmit={handleSubmit(onSubmit)} noValidate>
            <Controller
              name="password"
              control={control}
              rules={{
                required: tAuth('login.errors.passwordRequired'),
                pattern: {
                  value: /^(?=.*[A-Z])(?=.*[!@#$%^&*])(?=.*\d)[A-Za-z\d!@#$%^&*]{8,}$/,
                  message: tAuth('validation.passwordRequirements'),
                },
              }}
              render={({ field }) => (
                <TextField
                  label={tAuth('login.password')}
                  type={showPassword ? 'text' : 'password'}
                  fullWidth
                  margin="normal"
                  {...field}
                  error={!!errors.password}
                  helperText={errors.password?.message}
                  slotProps={{
                    input: {
                      endAdornment: (
                        <InputAdornment position="end">
                          <IconButton onClick={() => setShowPassword((prev) => !prev)} edge="end">
                            {showPassword ? <VisibilityOff /> : <Visibility />}
                          </IconButton>
                        </InputAdornment>
                      ),
                    },
                  }}
                />
              )}
            />

            <Controller
              name="confirmPassword"
              control={control}
              rules={{
                required: tAuth('resetPassword.errors.confirmPasswordRequired'),
                validate: (value) =>
                  value === password || tAuth('resetPassword.errors.passwordsMismatch'),
              }}
              render={({ field }) => (
                <TextField
                  label={tAuth('resetPassword.confirmPassword')}
                  type={showConfirmPassword ? 'text' : 'password'}
                  fullWidth
                  margin="normal"
                  {...field}
                  error={!!errors.confirmPassword}
                  helperText={errors.confirmPassword?.message}
                  slotProps={{
                    input: {
                      endAdornment: (
                        <InputAdornment position="end">
                          <IconButton
                            onClick={() => setConfirmShowPassword((prev) => !prev)}
                            edge="end"
                          >
                            {showConfirmPassword ? <VisibilityOff /> : <Visibility />}
                          </IconButton>
                        </InputAdornment>
                      ),
                    },
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
            >
              {tAuth('resetPassword.title')}
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
