import { Box, Paper, IconButton } from '@mui/material';
import { Email } from '@mui/icons-material';
import ReactMarkdown from 'react-markdown';
import { ChatEmailPayload, EmailData, MessagesType } from '@/types/types';
import { Dispatch, memo, SetStateAction, useState } from 'react';
import MarkdownComponents from '@/components/Chat/MarkdownComponent';
import EmailDialog from './EmailDialog';
import { sendEmail } from '@/services/api';
import { enqueueSnackbar } from 'notistack';
import { useTranslations } from '@/i18n/hooks/useTranslations';

type Props = {
  msg: MessagesType;
  isMobile: boolean;
  setLocalData: Dispatch<SetStateAction<Record<string, MessagesType[]>>>;
};

function Message({ msg, isMobile, setLocalData }: Props) {
  const [emailModalOpen, setEmailModalOpen] = useState(false);
  const [emailData, setEmailData] = useState<EmailData>({
    to: [],
    cc: [],
    bcc: [],
    subject: '',
    message: msg.response || '',
    isAlreadySent: false,
  });
  const [isSendMailLoading, setIsSendMailLoading] = useState<boolean>(false);

  const { t: tChat } = useTranslations('chat');

  const handleEmailOpen = () => {
    setEmailData({
      to: msg.metadata.email_output?.email_data?.to || [],
      cc: msg.metadata.email_output?.email_data?.cc || [],
      bcc: msg.metadata.email_output?.email_data?.bcc || [],
      subject: msg.metadata.email_output?.email_data?.subject || '',
      message: msg.metadata.email_output?.email_data?.body || '',
      isAlreadySent: msg.metadata.email_output?.email_data?.send_now || false,
    });
    setEmailModalOpen(true);
  };

  const handleEmailClose = () => {
    setEmailModalOpen(false);
    setEmailData({
      to: [],
      cc: [],
      bcc: [],
      subject: '',
      message: msg.response || '',
      isAlreadySent: false,
    });
  };

  const handleEmailFieldChange = (field: string, value: string[] | string) => {
    setEmailData((prev) => ({
      ...prev,
      [field]: value,
    }));
  };

  const handleSendEmail = async () => {
    setIsSendMailLoading(true);
    try {
      const payload: ChatEmailPayload = {
        email_data: {
          to: emailData.to.map((x) => x.trim()),
          cc: emailData.cc.map((x) => x.trim()),
          bcc: emailData.bcc.map((x) => x.trim()),
          subject: emailData.subject,
          body: emailData.message,
          session_id: msg.session_id,
          message_id: msg.id,
          send_now: true,
        },
      };
      const result = await sendEmail(payload);
      if (result.status === 200) {
        enqueueSnackbar(tChat('emailDialog.response.sent'), { variant: 'success' });
        setEmailData((prev) => ({
          ...prev,
          isAlreadySent: true,
        }));
        setLocalData((prev) => {
          const updatedMessages = prev[msg.session_id].map((m) => {
            if (m.id === msg.id && m.metadata?.email_output?.email_data) {
              m.metadata.email_output.email_data.send_now = true;
            }
            return m;
          });
          return { ...prev, [msg.session_id]: updatedMessages };
        });
      }
      handleEmailClose();
    } catch (error) {
      enqueueSnackbar(tChat('emailDialog.response.error'), { variant: 'error' });
    } finally {
      setIsSendMailLoading(false);
    }
  };

  return (
    <>
      {/* User Message */}
      {msg.message && (
        <Box
          sx={{
            display: 'flex',
            justifyContent: 'flex-end',
            mb: 2,
            maxWidth: '100%',
          }}
        >
          <Paper
            elevation={2}
            sx={{
              p: 2,
              maxWidth: isMobile ? '90%' : '70%',
              bgcolor: '#FFF',
              color: 'inherit',
              borderRadius: '10px 0px 10px 10px',
              boxShadow: '0px 2px 4px rgba(0,0,0,0.05)',
              transition: 'all 0.2s ease-in-out',
              '&:hover': {
                boxShadow: '0px 4px 8px rgba(0,0,0,0.1)',
              },
            }}
          >
            <ReactMarkdown components={MarkdownComponents(true)}>
              {msg.message.replace('/email', '').replace('/inbox', '')}
            </ReactMarkdown>
          </Paper>
        </Box>
      )}

      {/* Bot Response */}
      {msg.response && (
        <Box>
          <Box
            sx={{
              display: 'flex',
              justifyContent: 'flex-start',
              mb: 2,
              maxWidth: '100%',
            }}
          >
            <Box sx={{ maxWidth: isMobile ? '90%' : '70%' }}>
              <Paper
                elevation={2}
                sx={{
                  p: 2,
                  bgcolor: '#5b7bc0',
                  color: 'white',
                  borderRadius: '0px 10px 10px 10px',
                  boxShadow: '0px 2px 4px rgba(0,0,0,0.05)',
                  transition: 'all 0.2s ease-in-out',
                  '&:hover': {
                    boxShadow: '0px 4px 8px rgba(0,0,0,0.1)',
                  },
                }}
              >
                <ReactMarkdown components={MarkdownComponents(false)}>
                  {msg.response.replace('/email', '').replace('/inbox', '')}
                </ReactMarkdown>
              </Paper>
              {msg.metadata.email_output?.email_data && (
                <Box
                  sx={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: 1,
                    mt: 1,
                    pl: 1,
                  }}
                >
                  <IconButton
                    size="small"
                    onClick={handleEmailOpen}
                    sx={{
                      color: 'text.secondary',
                      '&:hover': {
                        bgcolor: 'action.hover',
                      },
                    }}
                  >
                    <Email fontSize="small" />
                  </IconButton>
                </Box>
              )}
            </Box>
          </Box>
        </Box>
      )}
      <EmailDialog
        emailModalOpen={emailModalOpen}
        handleEmailClose={handleEmailClose}
        emailData={emailData}
        handleEmailFieldChange={handleEmailFieldChange}
        handleSendEmail={handleSendEmail}
        isSendMailLoading={isSendMailLoading}
      />
    </>
  );
}

export default memo(Message);
