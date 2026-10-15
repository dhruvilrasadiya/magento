import json
import smtplib
import imaplib
import email
from email.header import decode_header
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import Any, Dict, Optional, List
from datetime import datetime
import base64
import re

from langchain_core.messages import HumanMessage, SystemMessage

from ..state.agent_state import AgentState
from ..utils.llm_utils import LLMConfig


class EmailAgent:
    """Agent that handles email composition, generation, and inbox management via natural language interface."""

    def __init__(self, llm_config: LLMConfig, email_config: Optional[Dict] = None):
        self.llm = llm_config.get_llm()
        self.email_config = email_config or {}
        self.imap_client = None

        # SMTP configuration
        self.smtp_server = self.email_config.get("smtp_server", "smtp.gmail.com")
        self.smtp_port = self.email_config.get("smtp_port", 587)
        self.email_from = self.email_config.get("email")
        self.email_password = self.email_config.get("password")

        # IMAP configuration
        self.imap_server = self.email_config.get("imap_server", "imap.gmail.com")
        self.imap_port = self.email_config.get("imap_port", 993)

    def _send_email(
        self,
        to_emails: List[str],
        subject: str,
        body: str,
        cc_emails: List[str] = None,
        bcc_emails: List[str] = None,
    ) -> bool:
        """Send email using SMTP with the reliable authentication method."""

        try:
            # Create message
            message = MIMEMultipart()
            message["From"] = self.email_from
            message["To"] = ", ".join(to_emails)
            message["Subject"] = subject

            if cc_emails:
                message["Cc"] = ", ".join(cc_emails)

            # Add body to email
            message.attach(MIMEText(body, "plain"))

            # Prepare recipient list
            recipients = to_emails.copy()
            if cc_emails:
                recipients.extend(cc_emails)
            if bcc_emails:
                recipients.extend(bcc_emails)

            # Send email using the reliable method
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.email_from, self.email_password)
            server.sendmail(self.email_from, recipients, message.as_string())
            server.quit()

            print(f"[SUCCESS] Email sent to {', '.join(recipients)}")
            return True

        except Exception as e:
            print(f"[ERROR] Failed to send email: {e}")
            return False

    def _setup_imap_connection(self) -> bool:
        """Setup IMAP connection for reading emails using the same credentials."""
        try:
            if not self.imap_server:
                print("[WARNING] No IMAP server configured")
                return False

            # Close existing connection if any
            if self.imap_client:
                try:
                    self.imap_client.close()
                    self.imap_client.logout()
                except:
                    pass

            # Create new connection
            self.imap_client = imaplib.IMAP4_SSL(self.imap_server, self.imap_port)
            self.imap_client.login(self.email_from, self.email_password)

            print("[SUCCESS] IMAP connection established")
            return True

        except Exception as e:
            print(f"[ERROR] Failed to setup IMAP connection: {str(e)}")
            self.imap_client = None
            return False

    def _test_connection(self) -> Dict[str, bool]:
        """Test both SMTP and IMAP connections."""
        results = {"smtp": False, "imap": False}

        # Test SMTP
        try:
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.email_from, self.email_password)
            server.quit()
            results["smtp"] = True
            print("[SUCCESS] SMTP connection test passed")
        except Exception as e:
            print(f"[ERROR] SMTP connection test failed: {e}")

        # Test IMAP
        try:
            if self._setup_imap_connection():
                results["imap"] = True
                self.imap_client.close()
                self.imap_client.logout()
                self.imap_client = None
        except Exception as e:
            print(f"[ERROR] IMAP connection test failed: {e}")

        return results

    def _get_inbox_emails(self, limit: int = 10, folder: str = "INBOX") -> List[Dict]:
        """Retrieve emails from inbox."""
        if not self.imap_client:
            if not self._setup_imap_connection():
                return []

        try:
            # Select the folder
            self.imap_client.select(folder)

            # Search for all emails
            status, messages = self.imap_client.search(None, "ALL")

            if status != "OK":
                print(f"[ERROR] Failed to search emails: {status}")
                return []

            # Get message IDs
            message_ids = messages[0].split()

            if not message_ids:
                print("[INFO] No emails found in inbox")
                return []

            # Get the latest emails (limit the number)
            latest_message_ids = (
                message_ids[-limit:] if len(message_ids) > limit else message_ids
            )

            emails = []
            for msg_id in reversed(latest_message_ids):  # Most recent first
                email_data = self._parse_email(msg_id)
                if email_data:
                    emails.append(email_data)

            print(f"[SUCCESS] Retrieved {len(emails)} emails from {folder}")
            return emails

        except Exception as e:
            print(f"[ERROR] Failed to retrieve emails: {str(e)}")
            return []

    def _parse_email(self, msg_id: bytes) -> Optional[Dict]:
        """Parse individual email message."""
        try:
            status, msg_data = self.imap_client.fetch(msg_id, "(RFC822)")

            if status != "OK":
                return None

            # Parse the email
            email_message = email.message_from_bytes(msg_data[0][1])

            # Extract headers
            subject = self._decode_header(email_message.get("Subject", ""))
            from_addr = self._decode_header(email_message.get("From", ""))
            to_addr = self._decode_header(email_message.get("To", ""))
            date = email_message.get("Date", "")

            # Extract body
            body = self._extract_body(email_message)

            return {
                "id": msg_id.decode(),
                "subject": subject,
                "from": from_addr,
                "to": to_addr,
                "date": date,
                "body": (
                    body[:500] + "..." if len(body) > 500 else body
                ),  # Truncate for preview
                "has_attachments": self._has_attachments(email_message),
            }

        except Exception as e:
            print(f"[ERROR] Failed to parse email: {str(e)}")
            return None

    def _decode_header(self, header: str) -> str:
        """Decode email header."""
        if not header:
            return ""

        try:
            decoded_header = decode_header(header)[0]
            if isinstance(decoded_header[0], bytes):
                return decoded_header[0].decode(decoded_header[1] or "utf-8")
            return decoded_header[0]
        except Exception as e:
            print(f"[WARNING] Failed to decode header: {e}")
            return str(header)

    def _extract_body(self, email_message) -> str:
        """Extract email body content."""
        body = ""

        try:
            if email_message.is_multipart():
                for part in email_message.walk():
                    content_type = part.get_content_type()
                    content_disposition = str(part.get("Content-Disposition", ""))

                    if (
                        content_type == "text/plain"
                        and "attachment" not in content_disposition
                    ):
                        try:
                            body = part.get_payload(decode=True).decode(
                                "utf-8", errors="ignore"
                            )
                            break
                        except:
                            continue
                    elif (
                        content_type == "text/html"
                        and not body
                        and "attachment" not in content_disposition
                    ):
                        try:
                            body = part.get_payload(decode=True).decode(
                                "utf-8", errors="ignore"
                            )
                            # Basic HTML stripping
                            body = re.sub(r"<[^>]+>", "", body)
                        except:
                            continue
            else:
                try:
                    body = email_message.get_payload(decode=True).decode(
                        "utf-8", errors="ignore"
                    )
                except:
                    body = str(email_message.get_payload())
        except Exception as e:
            print(f"[WARNING] Failed to extract body: {e}")
            body = "Failed to extract email body"

        return body.strip()

    def _has_attachments(self, email_message) -> bool:
        """Check if email has attachments."""
        try:
            if email_message.is_multipart():
                for part in email_message.walk():
                    content_disposition = str(part.get("Content-Disposition", ""))
                    if "attachment" in content_disposition:
                        return True
        except:
            pass
        return False

    def _search_emails(self, query: str, folder: str = "INBOX") -> List[Dict]:
        """Search emails based on criteria."""
        if not self.imap_client:
            if not self._setup_imap_connection():
                return []

        try:
            self.imap_client.select(folder)

            # Build search criteria based on query
            search_criteria = self._build_search_criteria(query)

            status, messages = self.imap_client.search(None, search_criteria)

            if status != "OK":
                print(f"[ERROR] Search failed: {status}")
                return []

            message_ids = messages[0].split()

            if not message_ids:
                print(f"[INFO] No emails found for query: {query}")
                return []

            emails = []
            for msg_id in reversed(message_ids[-20:]):  # Limit to 20 results
                email_data = self._parse_email(msg_id)
                if email_data:
                    emails.append(email_data)

            print(f"[SUCCESS] Found {len(emails)} emails for query: {query}")
            return emails

        except Exception as e:
            print(f"[ERROR] Failed to search emails: {str(e)}")
            return []

    def _build_search_criteria(self, query: str) -> str:
        """Build IMAP search criteria from natural language query."""
        query_lower = query.lower()

        # Extract email addresses
        email_pattern = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"
        emails = re.findall(email_pattern, query)

        # Check for common search terms
        if "from" in query_lower and emails:
            return f'FROM "{emails[0]}"'
        elif "to" in query_lower and emails:
            return f'TO "{emails[0]}"'
        elif "subject" in query_lower:
            # Extract subject keywords
            subject_match = re.search(r"subject[:\s]+([^,]+)", query_lower)
            if subject_match:
                return f'SUBJECT "{subject_match.group(1).strip()}"'
        elif "unread" in query_lower:
            return "UNSEEN"
        elif "today" in query_lower:
            return "SINCE " + datetime.now().strftime("%d-%b-%Y")
        elif "yesterday" in query_lower:
            yesterday = datetime.now().replace(day=datetime.now().day - 1)
            return f'ON {yesterday.strftime("%d-%b-%Y")}'
        else:
            # Default text search
            return f'TEXT "{query}"'

    def _build_system_prompt(
        self, context_prompt: str, is_inbox_query: bool = False
    ) -> str:
        base_prompt = f"""
        You are an Email Agent that helps users with email operations via natural language commands.

        Use the following CONTEXT when processing emails:
        {context_prompt}

        Your primary responsibilities:
        1. Parse user input for email operations (/email for compose, /inbox for reading)
        2. Generate structured JSON output for email operations
        3. Always return valid JSON regardless of input quality
        """

        if is_inbox_query:
            return (
                base_prompt
                + """
            For INBOX queries, return JSON in this format:
            {
                "inbox_operation": {
                    "action": "list|search|read",
                    "criteria": "search criteria if applicable",
                    "limit": 10,
                    "folder": "INBOX"
                }
            }

            Common inbox operations:
            - "show me latest emails" -> action: "list"
            - "search emails from john@example.com" -> action: "search", criteria: "from john@example.com"
            - "find emails about project" -> action: "search", criteria: "subject project"
            - "show unread emails" -> action: "search", criteria: "unread"
            
            STRICTLY return only valid JSON as shown above. Do NOT include markdown, explanation, or notes.
            """
            )
        else:
            return (
                base_prompt
                + """
            For EMAIL composition, return JSON in this format:
            {
                "email_data": {
                    "to": ["recipient1@example.com"],
                    "cc": ["cc1@example.com"],
                    "bcc": ["bcc1@example.com"],
                    "subject": "Email Subject",
                    "body": "Email body content",
                    "send_now": false
                }
            }

            Processing Rules:
            1. Extract email addresses using regex patterns
            2. If recipient is missing, set "to": []
            3. Generate a subject and body from the user query and context
            4. For the closing, replace [Your Name] with Tess Bot
            5. Set send_now to true if user explicitly requests immediate sending
            
            STRICTLY return only valid JSON as shown above. Do NOT include markdown, explanation, or notes.
            """
            )

    async def process_inbox_query(
        self, query: str, state: AgentState
    ) -> Dict[str, Any]:
        """Process an inbox query and return email data."""
        print(f"[INFO] EmailAgent: Processing inbox query: {query}")

        try:
            # Check connection first
            if not self._test_connection()["imap"]:
                return {"response": {"error": "Failed to connect to email server"}}

            # Get dynamic context from state
            context_prompt = (
                json.dumps(state.get("agent_outputs", "No context provided."))
                + "\n\n"
                + json.dumps(state.get("chat_history", ""))
            )

            # Parse the query using LLM
            inbox_operation = await self._parse_inbox_query_with_llm(
                query, context_prompt
            )

            if not inbox_operation:
                return {"response": {"error": "Failed to parse inbox query"}}

            # Execute the inbox operation
            if inbox_operation["action"] == "list":
                emails = self._get_inbox_emails(
                    limit=inbox_operation.get("limit", 10),
                    folder=inbox_operation.get("folder", "INBOX"),
                )
                return {
                    "response": {
                        "emails": emails,
                        "total": len(emails),
                        "action": "list",
                    }
                }

            elif inbox_operation["action"] == "search":
                emails = self._search_emails(
                    inbox_operation.get("criteria", ""),
                    folder=inbox_operation.get("folder", "INBOX"),
                )
                return {
                    "response": {
                        "emails": emails,
                        "total": len(emails),
                        "action": "search",
                    }
                }

            else:
                return {"response": {"error": "Unsupported inbox operation"}}

        except Exception as e:
            print(f"[ERROR] EmailAgent inbox query: {str(e)}")
            return {"response": {"error": str(e)}}

    async def _parse_inbox_query_with_llm(
        self, query: str, context_prompt: str
    ) -> Optional[Dict]:
        """Use LLM to parse inbox query."""
        try:
            system_prompt = self._build_system_prompt(
                context_prompt, is_inbox_query=True
            )

            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(
                    content=f"""
                        CONTEXT:
                        {context_prompt}

                        INBOX QUERY:
                        {query}

                        Generate a structured inbox operation JSON from this input.
                    """
                ),
            ]

            response = self.llm.invoke(messages)
            parsed_json = json.loads(response.content.strip())

            return parsed_json.get("inbox_operation", {})

        except Exception as e:
            print(f"[WARNING] EmailAgent inbox LLM parsing failed: {str(e)}")
            return None

    async def process_query(self, query: str, state: AgentState) -> Dict[str, Any]:
        """Process an email composition query and generate structured JSON output."""
        print(f"[INFO] EmailAgent: Processing composition query: {query}")

        try:
            # Get dynamic context from state
            context_prompt = (
                json.dumps(state.get("agent_outputs", "No context provided."))
                + "\n\n"
                + json.dumps(state.get("chat_history", ""))
            )
            enhanced_data = await self._enhance_with_llm(query, state, context_prompt)

            # Check if we should send the email immediately
            print(
                f"[INFO] state auto send email: {state.get('auto_send_email')} {type(state.get('auto_send_email'))}"
            )
            if enhanced_data and state.get("auto_send_email"):
                email_data = enhanced_data["email_data"]

                # Validate required fields
                if not email_data.get("to"):
                    return {"response": {"error": "No recipients specified"}}

                # Send the email
                success = self._send_email(
                    to_emails=email_data["to"],
                    subject=email_data["subject"],
                    body=email_data["body"],
                    cc_emails=email_data.get("cc", []),
                    bcc_emails=email_data.get("bcc", []),
                )

                enhanced_data["email_data"]["sent"] = success
                enhanced_data["email_data"]["send_now"] = success
                enhanced_data["email_data"]["sent_at"] = (
                    datetime.now().isoformat() if success else None
                )
            else:
                enhanced_data["email_data"]["send_now"] = False

            return {"response": enhanced_data}

        except Exception as e:
            print(f"[ERROR] EmailAgent: {str(e)}")
            error_result = {
                "email_data": {
                    "to": [],
                    "cc": [],
                    "bcc": [],
                    "subject": "",
                    "body": "",
                    "error": str(e),
                },
            }
            return {"response": error_result}

    async def _enhance_with_llm(
        self, query: str, state: AgentState, context_prompt: str
    ) -> Optional[Dict[str, Any]]:
        """Use LLM to enhance incomplete email data."""
        try:
            system_prompt = self._build_system_prompt(
                context_prompt, is_inbox_query=False
            )

            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(
                    content=f"""
                        CONTEXT:
                        {context_prompt}

                        QUERY:
                        {query}

                        Generate a structured email JSON from this input.
                    """
                ),
            ]

            response = self.llm.invoke(messages)
            enhanced_json = response.content.strip()

            print(f"[DEBUG] EmailAgent LLM Response: {enhanced_json}")
            return json.loads(enhanced_json)

        except Exception as e:
            print(f"[WARNING] EmailAgent LLM enhancement failed: {str(e)}")
            return None

    async def run(self, state: AgentState) -> AgentState:
        """Run the email agent and update the state."""
        print("-----" * 20)
        print(f"[START] Email Agent")

        # Test connection on first run
        if not hasattr(self, "_connection_tested"):
            connection_status = self._test_connection()
            print(
                f"[INFO] Connection status: SMTP={connection_status['smtp']}, IMAP={connection_status['imap']}"
            )
            self._connection_tested = True

        # Determine if this is an inbox query or composition query
        query = state["agent_queries"].get("email_agent", state.get("query"))
        is_inbox_query = "/inbox" in str(query).lower() or "inbox" in str(query).lower()

        results = {}

        if isinstance(query, list):
            for q in query:
                if "/inbox" in q.lower() or "inbox" in q.lower():
                    result = await self.process_inbox_query(q, state)
                else:
                    result = await self.process_query(q, state)
                results[q] = result["response"]
        else:
            if is_inbox_query:
                result = await self.process_inbox_query(query, state)
            else:
                result = await self.process_query(query, state)
            results[query] = result["response"]

        # Store results in agent outputs
        state["agent_outputs"]["email_agent"] = json.dumps(results)

        # Store structured result based on operation type
        if is_inbox_query:
            if "inbox_output" not in state:
                state["inbox_output"] = {}

            try:
                if isinstance(query, str):
                    state["inbox_output"] = result["response"]
                else:
                    state["inbox_output"] = {"multiple_queries": results}
            except Exception:
                state["inbox_output"] = {"error": "Failed to parse inbox data"}
        else:
            if "email_output" not in state:
                state["email_output"] = {}

            try:
                if isinstance(query, str):
                    email_result = result["response"]
                    state["email_output"] = email_result
                else:
                    state["email_output"] = {"multiple_emails": results}
            except Exception:
                state["email_output"] = {"error": "Failed to parse email JSON"}

        # Mark email agent as executed
        state["email_agent_executed"] = True

        print(f"[END] Email Agent")
        print("-----" * 20)

        return state

    def __del__(self):
        """Cleanup IMAP connection."""
        if self.imap_client:
            try:
                self.imap_client.close()
                self.imap_client.logout()
            except:
                pass
