import json
import os
from datetime import datetime
from typing import Any, Dict, List

from utils import EmbeddingManager


class CRMDataProcessor:
    """Processes CRM data, including blogs and support tickets."""

    def __init__(self, embedding_manager: EmbeddingManager):
        self.embedding_manager = embedding_manager

    def process_blog_post(self, blog_post: Dict[str, Any]) -> Dict[str, Any]:
        """Process a single blog post."""
        return {
            "content": (
                f"Title: {blog_post.get('title', '')}\n"
                f"Content: {blog_post.get('content', '')}"
            ),
            "metadata": {
                "type": "blog",
                "id": blog_post.get("id"),
                "title": blog_post.get("title"),
                "author": blog_post.get("author"),
                "publish_date": blog_post.get("publish_date"),
                "timestamp": datetime.now().isoformat(),
            },
        }

    def process_support_ticket(self, ticket: Dict[str, Any]) -> Dict[str, Any]:
        """Process a single support ticket."""
        return {
            "content": (
                f"Subject: {ticket.get('subject', '')}\n"
                f"Description: {ticket.get('description', '')}\n"
                f"Resolution: {ticket.get('resolution', '')}"
            ),
            "metadata": {
                "type": "ticket",
                "id": ticket.get("id"),
                "status": ticket.get("status"),
                "priority": ticket.get("priority"),
                "created_at": ticket.get("created_at"),
                "resolved_at": ticket.get("resolved_at"),
                "timestamp": datetime.now().isoformat(),
            },
        }

    def process_crm_data(
        self, blog_posts: List[Dict[str, Any]], support_tickets: List[Dict[str, Any]]
    ) -> bool:
        """Process and embed CRM data."""
        try:
            processed_items = []

            # Process blog posts
            for post in blog_posts:
                processed_items.append(self.process_blog_post(post))

            # Process support tickets
            for ticket in support_tickets:
                processed_items.append(self.process_support_ticket(ticket))

            if not processed_items:
                print("No CRM data to process")
                return False

            # Prepare data for embedding
            texts = [item["content"] for item in processed_items]
            metadata = [item["metadata"] for item in processed_items]

            # Store embeddings
            success = self.embedding_manager.store_embeddings(
                data_type="crm", texts=texts, metadata=metadata
            )

            return success

        except Exception as e:
            print(f"Error processing CRM data: {str(e)}")
            return False


def embed_crm_data(**context):
    """Airflow task to process CRM data."""
    try:
        # Initialize components
        embedding_manager = EmbeddingManager()
        processor = CRMDataProcessor(embedding_manager)

        # Get input data paths from Airflow config
        blog_data_path = context["dag_run"].conf.get(
            "blog_data_path", "/data/blogs/latest.json"
        )
        ticket_data_path = context["dag_run"].conf.get(
            "ticket_data_path", "/data/tickets/latest.json"
        )

        # Load data
        blog_posts = []
        support_tickets = []

        if os.path.exists(blog_data_path):
            with open(blog_data_path, "r") as f:
                blog_posts = json.load(f)

        if os.path.exists(ticket_data_path):
            with open(ticket_data_path, "r") as f:
                support_tickets = json.load(f)

        # Process data
        success = processor.process_crm_data(blog_posts, support_tickets)

        if not success:
            raise Exception("CRM data processing failed")

        return True

    except Exception as e:
        print(f"Error in CRM data processing task: {str(e)}")
        raise
