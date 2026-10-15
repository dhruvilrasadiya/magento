import os
import uuid
from datetime import datetime
from typing import Any, Dict, List

from PyPDF2 import PdfReader
from langchain_core.documents import Document
from utils.embed_utils import embed_and_upsert_pdfs  # Ensure this exists and works


def extract_chunks_from_pdf(pdf_path: str) -> List[Dict[str, Any]]:
    """Extract text chunks and metadata from a PDF file."""
    try:
        reader = PdfReader(pdf_path)
        chunks = []

        for page_num in range(len(reader.pages)):
            page = reader.pages[page_num]
            text = page.extract_text()

            if not text:
                continue

            chunk_size = 1000
            words = text.split()

            for i in range(0, len(words), chunk_size):
                chunk = " ".join(words[i: i + chunk_size])
                if chunk.strip():
                    chunks.append({
                        "content": chunk,
                        "metadata": {
                            "file_name": os.path.basename(pdf_path),
                            "file_path": pdf_path,
                            "page_num": page_num + 1,
                            "chunk_num": len(chunks) + 1,
                            "timestamp": datetime.now().isoformat(),
                        },
                    })

        return chunks

    except Exception as e:
        print(f"[ERROR] Failed to process {pdf_path}: {str(e)}")
        return []


def process_pdf_directory(directory_path: str) -> List[Document]:
    """Process all PDF files in a directory and convert them into LangChain documents."""
    try:
        pdf_files = [
            os.path.join(directory_path, f)
            for f in os.listdir(directory_path)
            if f.lower().endswith(".pdf")
        ]

        all_docs = []
        all_doc_logs = {}

        for pdf_file in pdf_files:
            chunks = extract_chunks_from_pdf(pdf_file)
            doc_log: Dict[str, List[str]] = {}
            file_name = os.path.basename(pdf_file)

            single_file_docs = []
            for chunk in chunks:
                doc_uuid = str(uuid.uuid4())
                metadata = chunk["metadata"]
                metadata["type"] = "pdf_chunk"
                metadata["doc_id"] = doc_uuid

                doc = Document(
                    page_content=chunk["content"],
                    metadata=metadata
                )
                single_file_docs.append(doc)

                doc_log.setdefault("pdf_chunk", []).append(doc_uuid)

            if single_file_docs:
                print(f"[PROCESS] Processed {file_name} into {len(single_file_docs)} chunks.")
                all_doc_logs[file_name] = doc_log
                all_docs.extend(single_file_docs)

        print(f"[INFO] Total {len(all_docs)} documents processed from {len(pdf_files)} PDFs.")
        embed_and_upsert_pdfs(all_docs, all_doc_logs)

        return all_docs

    except Exception as e:
        print(f"[ERROR] Failed to process directory {directory_path}: {str(e)}")
        return []


def process_pdfs(**context):
    """Airflow-compatible function to process PDFs and upsert their embeddings."""
    try:
        # Set default input directory as scripts/data relative to this script
        input_directory = context["dag_run"].conf.get(
            "input_directory", "/opt/airflow/data")

        if not os.path.exists(input_directory):
            raise FileNotFoundError(f"Input directory {input_directory} does not exist.")

        docs = process_pdf_directory(input_directory)
        if not docs:
            raise Exception("No documents were created from PDF processing.")

        return True

    except Exception as e:
        print(f"[ERROR] PDF ingestion failed: {str(e)}")
        raise
