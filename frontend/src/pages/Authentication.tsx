import { useEffect, useState } from 'react';
import { Container } from '@mui/material';
import { FormType } from '@/types/types';
import { useAuth } from '@/hooks/useAuth';
import { Navigate } from 'react-router-dom';
import ForgetPasswordForm from '@/components/ForgetPassword/Form';
import LoginForm from '@/components/Login/Form';
import LoginHeader from '@/components/Login/Header';
import ResetPasswordForm from '@/components/ResetPassword/Form';
import { routes } from '@/constants/routes';

function Authentication() {
  const [formType, setFormType] = useState<FormType>('Login');
  const { isAuthenticated } = useAuth();

  useEffect(() => {
    if (window.location.search.includes('reset-password')) {
      setFormType('ResetPassword');
    }
  }, []);

  if (isAuthenticated) {
    return <Navigate to={routes.home} replace />;
  }

  return (
    <>
      <LoginHeader />
      <Container>
        {formType === 'Login' ? (
          <LoginForm setFormType={setFormType} />
        ) : formType === 'ForgetPassword' ? (
          <ForgetPasswordForm setFormType={setFormType} />
        ) : (
          <ResetPasswordForm setFormType={setFormType} />
        )}
      </Container>
    </>
  );
}

export default Authentication;
