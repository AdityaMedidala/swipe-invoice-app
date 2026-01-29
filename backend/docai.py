import os
from google.cloud import documentai_v1 as documentai
from google.api_core.client_options import ClientOptions

# Config
PROJECT_ID = "compact-factor-485705-g9"
LOCATION = "us"
PROCESSOR_ID = "527767b94fb85b37"
SERVICE_ACCOUNT_PATH = "service-account-key.json"


def get_client():
    """Initialize Document AI client"""
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = SERVICE_ACCOUNT_PATH
    
    opts = ClientOptions(api_endpoint=f"{LOCATION}-documentai.googleapis.com")
    client = documentai.DocumentProcessorServiceClient(client_options=opts)
    
    return client


def process_document(file_bytes: bytes, mime_type: str):
    """Process document using Google Document AI"""
    client = get_client()
    
    # Build processor path
    name = client.processor_path(PROJECT_ID, LOCATION, PROCESSOR_ID)
    
    # Create request
    raw_document = documentai.RawDocument(content=file_bytes, mime_type=mime_type)
    request = documentai.ProcessRequest(name=name, raw_document=raw_document)
    
    # Process document
    result = client.process_document(request=request)
    
    return result.document