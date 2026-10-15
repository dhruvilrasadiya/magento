import {
  Box,
  Button,
  IconButton,
  InputAdornment,
  Link,
  TextField,
  Typography,
} from '@mui/material';
import { Visibility, VisibilityOff } from '@mui/icons-material';
import { Dispatch, SetStateAction, useState } from 'react';
import { useForm, Controller } from 'react-hook-form';
import Grid from '@mui/material/Grid';
import SideImage from '@/assets/images/login_1.png';
import { useNavigate } from 'react-router-dom';
import { FormType } from '@/types/types';
import { useAuth } from '@/hooks/useAuth';
import { useTranslations } from '@/i18n/hooks/useTranslations';
import { routes } from '@/constants/routes';

type FormValues = {
  userName: string;
  password: string;
};

type Props = {
  setFormType: Dispatch<SetStateAction<FormType>>;
};

export default function LoginPage({ setFormType }: Props) {
  const {
    control,
    handleSubmit,
    formState: { errors },
  } = useForm<FormValues>({
    defaultValues: {
      userName: '',
      password: '',
    },
  });

  const [showPassword, setShowPassword] = useState<boolean>(false);
  const { login } = useAuth();
  const [loading, setLoading] = useState<boolean>(false);
  const navigate = useNavigate();
  const { t: tAuth } = useTranslations('auth');

  const onSubmit = async (data: FormValues) => {
    try {
      setLoading(true);
      const payload = {
        username: data.userName,
        password: data.password,
      };
      const result = await login(payload);
      if (result) {
        setTimeout(() => {
          navigate(routes.home, { replace: true });
        }, 100);
      }
      setLoading(false);
    } catch (error) {
      setLoading(false);
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
            {tAuth('login.title')}
          </Typography>
          <Typography color="text.secondary" mb={3}>
            {tAuth('login.description')}
          </Typography>

          <form onSubmit={handleSubmit(onSubmit)} noValidate>
            <Controller
              name="userName"
              control={control}
              rules={{ required: tAuth('login.errors.usernameRequired') }}
              render={({ field }) => (
                <TextField
                  label={tAuth('login.username')}
                  fullWidth
                  margin="normal"
                  {...field}
                  error={!!errors.userName}
                  helperText={errors.userName?.message}
                />
              )}
            />

            <Controller
              name="password"
              control={control}
              rules={{ required: tAuth('login.errors.passwordRequired') }}
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

            <Box display="flex" justifyContent="end" alignItems="center" mt={1}>
              <Link onClick={() => setFormType('ForgetPassword')} href="#" underline="hover">
                {tAuth('login.forgotPassword')}
              </Link>
            </Box>

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
              {tAuth('login.title')}
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
