import {
  Box,
  Button,
  Grid,
  MenuItem,
  TextField,
  Typography,
  FormControl,
  InputLabel,
  Select,
  InputAdornment,
  IconButton,
} from '@mui/material';
import { useForm, Controller } from 'react-hook-form';
import { createUser, updateUser } from '@/services/api';
import { CreateUserPayload, GetUsersType, Role, UserTokenPayload } from '@/types/types';
import { enqueueSnackbar } from 'notistack';
import { Visibility, VisibilityOff } from '@mui/icons-material';
import { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { hasPermission } from '@/utils/hasPermission';
import { useAuth } from '@/hooks/useAuth';
import { jwtDecode } from 'jwt-decode';
import { useTranslations } from '@/i18n/hooks/useTranslations';
import { routes } from '@/constants/routes';

type FormValues = {
  name: string;
  email: string;
  password: string;
  role: Role;
};

export default function UserManagement() {
  const [showPassword, setShowPassword] = useState<boolean>(false);
  const navigate = useNavigate();
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const { user: User } = useAuth();
  const [searchParams] = useSearchParams();
  const jwtPayload = jwtDecode<UserTokenPayload>(User?.token!);
  const { t: tCommon } = useTranslations('common');
  const { t: tAuth } = useTranslations('auth');
  const { t: tUsers } = useTranslations('users');

  const menuItems = [
    {
      value: 'admin',
      label: 'userManagement.role.types.admin',
      condition: hasPermission(jwtPayload.role as Role, 'create:admin'),
    },
    { value: 'supervisor', label: 'userManagement.role.types.supervisor' },
    // { value: 'user', label: 'User', disabled: true },
    // { value: 'moderator', label: 'Moderator', disabled: true },
  ];

  const userStr = searchParams.get('user');
  const userData: GetUsersType = userStr ? JSON.parse(decodeURIComponent(userStr)) : null;

  const [user, setUser] = useState(userData);

  const defaultValues = {
    name: user?.username || '',
    email: user?.email || '',
    password: user?.password || '',
    role: user?.role || '',
  };

  const {
    control,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<FormValues>({
    defaultValues,
  });

  useEffect(() => {
    if (user) {
      reset({
        name: user.username || '',
        email: user.email || '',
        password: user.password || '',
        role: user.role || '',
      });
    }
  }, [user, reset]);

  const onSubmit = async (data: FormValues) => {
    setIsLoading(true);
    try {
      let result;

      if (!user) {
        const payload: CreateUserPayload = {
          ...data,
          username: data.name,
        };

        result = await createUser(payload);
      } else {
        const updateUserPayload: GetUsersType = {
          ...data,
          id: user.id,
          username: data.name,
          created_at: new Date(),
        };
        result = await updateUser(updateUserPayload);
      }

      if (result && result.status === 200) {
        enqueueSnackbar(user ? tUsers('success.userUpdated') : tUsers('success.userAdded'), {
          variant: 'success',
        });
        if (user) {
          setUser(result.data);
          navigate(
            routes.userManagement + `?user=${encodeURIComponent(JSON.stringify(result.data))}`,
            {
              replace: true,
            }
          );
        }
        reset();
      }
      setIsLoading(false);
    } catch (error: any) {
      setIsLoading(false);
      console.log(error);
      const errorMessage =
        error.response?.data?.detail === 'Username already exists'
          ? tUsers('errors.userAlreadyExists')
          : error.response?.data?.detail === 'User not found'
          ? tUsers('errors.userNotFound')
          : error.response?.data?.detail === 'Email already registered'
          ? tUsers('errors.emailRegistered')
          : tUsers('errors.creatingUser');
      enqueueSnackbar(`${errorMessage}`, {
        variant: 'error',
      });
    }
  };

  return (
    <Box
      padding={{ xs: 2, md: 5 }}
      sx={{ backgroundColor: '#F0F5FA', height: '100vh', width: '100%' }}
    >
      <Box
        maxWidth={{ xs: '100vw', md: '55vw' }}
        mt={8}
        px={{ xs: 2.5, md: 5 }}
        py={5}
        borderRadius={2}
        border={1}
        borderColor={'lightgray'}
        bgcolor={'white'}
      >
        <Typography variant="h5" pb={5} fontWeight={600} gutterBottom>
          {user ? tUsers('actions.editUser') : tUsers('actions.createUser')}
        </Typography>

        <form onSubmit={handleSubmit(onSubmit)} noValidate>
          <Grid container spacing={2} mt={1}>
            <Grid size={{ xs: 12 }}>
              <Controller
                name="name"
                control={control}
                rules={{ required: tAuth('validation.nameRequired') }}
                render={({ field }) => (
                  <TextField
                    fullWidth
                    label={tCommon('form.name')}
                    {...field}
                    error={!!errors.name}
                    helperText={errors.name?.message}
                  />
                )}
              />
            </Grid>

            <Grid size={{ xs: 12, md: 6 }}>
              <Controller
                name="email"
                control={control}
                rules={{
                  required: tAuth('validation.emailRequired'),
                  pattern: {
                    value: /^[^\s@]+@[^\s@]+\.[^\s@]+$/,
                    message: tAuth('validation.invalidEmail'),
                  },
                }}
                render={({ field }) => (
                  <TextField
                    fullWidth
                    label={tCommon('form.email')}
                    {...field}
                    error={!!errors.email}
                    helperText={errors.email?.message}
                  />
                )}
              />
            </Grid>

            <Grid size={{ xs: 12, md: 6 }}>
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
                    fullWidth
                    label={tAuth('login.password')}
                    type={showPassword ? 'text' : 'password'}
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
                disabled={user ? true : false}
              />
            </Grid>

            <Grid size={{ xs: 12 }}>
              <Controller
                name="role"
                control={control}
                rules={{ required: tAuth('validation.roleRequired') }}
                render={({ field }) => (
                  <FormControl fullWidth error={!!errors.role}>
                    <InputLabel>{tUsers('userManagement.role.label')}</InputLabel>
                    <Select {...field} label={tUsers('userManagement.role.label')}>
                      {menuItems.map(
                        (item) =>
                          (item.condition === undefined || item.condition) && (
                            <MenuItem key={item.value} value={item.value}>
                              {tUsers(item.label)}
                            </MenuItem>
                          )
                      )}
                    </Select>
                    <Typography variant="caption" color="error" sx={{ mt: 0.5, ml: 1 }}>
                      {errors.role?.message}
                    </Typography>
                  </FormControl>
                )}
              />
            </Grid>

            <Grid size={{ xs: 12 }} display="flex" gap={2} mt={2}>
              <Button
                type="submit"
                variant="contained"
                loading={isLoading}
                sx={{
                  px: { xs: 3.5, md: 7 },
                  py: 1.5,
                  backgroundColor: '#003399',
                  fontWeight: 'bold',
                }}
              >
                {tCommon('form.save')}
              </Button>
              <Button
                variant="outlined"
                onClick={() => reset()}
                sx={{
                  px: { xs: 3.5, md: 7 },
                  py: 1.5,
                  fontWeight: 'bold',
                }}
                disabled={isLoading}
              >
                {tCommon('form.cancel')}
              </Button>
            </Grid>
          </Grid>
        </form>
      </Box>
    </Box>
  );
}
