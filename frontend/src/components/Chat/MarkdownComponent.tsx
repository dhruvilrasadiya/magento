const markdownStyles = {
  // Headers
  h1: {
    fontSize: '1.8rem',
    fontWeight: 600,
    marginTop: '16px',
    marginBottom: '12px',
    borderBottom: '1px solid rgba(0,0,0,0.1)',
    paddingBottom: '8px',
  },
  h2: {
    fontSize: '1.5rem',
    fontWeight: 600,
    marginTop: '14px',
    marginBottom: '10px',
  },
  h3: {
    fontSize: '1.2rem',
    fontWeight: 600,
    marginTop: '12px',
    marginBottom: '8px',
  },
  // Lists
  ul: {
    paddingLeft: '20px',
    marginTop: '8px',
    marginBottom: '8px',
  },
  ol: {
    paddingLeft: '20px',
    marginTop: '8px',
    marginBottom: '8px',
  },
  li: {
    marginBottom: '4px',
  },
  // Code blocks
  code: {
    backgroundColor: 'rgba(0,0,0,0.06)',
    padding: '2px 4px',
    borderRadius: '4px',
    fontFamily: '"Roboto Mono", monospace',
    fontSize: '0.9em',
  },
  pre: {
    backgroundColor: 'rgba(0,0,0,0.06)',
    padding: '12px',
    borderRadius: '4px',
    overflowX: 'auto',
    marginTop: '8px',
    marginBottom: '8px',
  },
  // Blockquotes
  blockquote: {
    borderLeft: '4px solid rgba(0,0,0,0.2)',
    paddingLeft: '12px',
    marginLeft: '0',
    color: 'rgba(0,0,0,0.6)',
    fontStyle: 'italic',
  },
  // Links
  a: {
    color: '#3f51b5',
    textDecoration: 'none',
    '&:hover': {
      textDecoration: 'underline',
    },
  },
  // Table styles
  table: {
    borderCollapse: 'collapse',
    width: '100%',
    marginTop: '12px',
    marginBottom: '12px',
  },
  th: {
    borderBottom: '2px solid rgba(0,0,0,0.1)',
    padding: '8px 12px',
    textAlign: 'left',
  },
  td: {
    borderBottom: '1px solid rgba(0,0,0,0.1)',
    padding: '8px 12px',
  },
  // Horizontal rule
  hr: {
    border: 'none',
    height: '1px',
    backgroundColor: 'rgba(0,0,0,0.1)',
    margin: '16px 0',
  },
  // Image rule
};

// Custom components for ReactMarkdown
const MarkdownComponents = (isUserMessage: boolean) => ({
  h1: ({ node, ...props }: any) => (
    <h1
      style={{
        ...markdownStyles.h1,
        color: isUserMessage ? 'inherit' : 'white',
      }}
      {...props}
    />
  ),
  h2: ({ node, ...props }: any) => (
    <h2
      style={{
        ...markdownStyles.h2,
        color: isUserMessage ? 'inherit' : 'white',
      }}
      {...props}
    />
  ),
  h3: ({ node, ...props }: any) => (
    <h3
      style={{
        ...markdownStyles.h3,
        color: isUserMessage ? 'inherit' : 'white',
      }}
      {...props}
    />
  ),
  ul: ({ node, ...props }: any) => <ul style={markdownStyles.ul} {...props} />,
  ol: ({ node, ...props }: any) => <ol style={markdownStyles.ol} {...props} />,
  li: ({ node, ...props }: any) => <li style={markdownStyles.li} {...props} />,
  code: ({ node, inline, ...props }: any) =>
    inline ? (
      <code
        style={{
          ...markdownStyles.code,
          backgroundColor: isUserMessage ? 'rgba(0,0,0,0.06)' : 'rgba(255,255,255,0.2)',
        }}
        {...props}
      />
    ) : (
      <code {...props} />
    ),
  pre: ({ node, ...props }: any) => (
    <pre
      style={{
        ...markdownStyles.pre,
        backgroundColor: isUserMessage ? 'rgba(0,0,0,0.06)' : 'rgba(255,255,255,0.1)',
      }}
      {...props}
    />
  ),
  blockquote: ({ node, ...props }: any) => (
    <blockquote
      style={{
        ...markdownStyles.blockquote,
        borderLeftColor: isUserMessage ? 'rgba(0,0,0,0.2)' : 'rgba(255,255,255,0.4)',
        color: isUserMessage ? 'rgba(0,0,0,0.6)' : 'rgba(255,255,255,0.8)',
      }}
      {...props}
    />
  ),
  a: ({ node, ...props }: any) => (
    <a
      style={{
        ...markdownStyles.a,
        color: isUserMessage ? '#3f51b5' : '#b3e5fc',
      }}
      {...props}
    />
  ),
  table: ({ node, ...props }: any) => <table style={markdownStyles.table} {...props} />,
  th: ({ node, ...props }: any) => (
    <th
      style={{
        ...markdownStyles.th,
        borderBottomColor: isUserMessage ? 'rgba(0,0,0,0.1)' : 'rgba(255,255,255,0.2)',
      }}
      {...props}
    />
  ),
  td: ({ node, ...props }: any) => (
    <td
      style={{
        ...markdownStyles.td,
        borderBottomColor: isUserMessage ? 'rgba(0,0,0,0.1)' : 'rgba(255,255,255,0.1)',
      }}
      {...props}
    />
  ),
  hr: ({ node, ...props }: any) => (
    <hr
      style={{
        ...markdownStyles.hr,
        backgroundColor: isUserMessage ? 'rgba(0,0,0,0.1)' : 'rgba(255,255,255,0.2)',
      }}
      {...props}
    />
  ),
  img: ({ node, ...props }: any) => (
  <img
    style={{
      maxWidth: '265px',
      maxHeight: '265px',
      objectFit: 'contain',
      display: 'block',
      marginTop: '8px',
      marginBottom: '8px',
    }}
    {...props}
  />
),

});

export default MarkdownComponents;
