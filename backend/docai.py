import os
from google.cloud import documentai_v1 as documentai
from google.api_core.client_options import ClientOptions


# ----------------------------
# CONFIG  (VERIFY THESE!)
# ----------------------------

PROJECT_ID = "compact-factor-485705-g9"   # MUST match console
LOCATION = "us"
PROCESSOR_ID = "527767b94fb85b37"

SERVICE_ACCOUNT_PATH = "service-account-key.json"

print("\n========== DOCAI.PY: MODULE LOADED ==========")
print(f"[DOCAI-CONFIG] PROJECT_ID: {PROJECT_ID}")
print(f"[DOCAI-CONFIG] LOCATION: {LOCATION}")
print(f"[DOCAI-CONFIG] PROCESSOR_ID: {PROCESSOR_ID}")
print(f"[DOCAI-CONFIG] SERVICE_ACCOUNT_PATH: {SERVICE_ACCOUNT_PATH}")
print("========================================\n")


# ----------------------------
# INIT CLIENT
# ----------------------------

def get_client():
    print("\n---------- DOCAI.PY: get_client() STARTED ----------")
    print(f"[DOCAI-CLIENT] Setting GOOGLE_APPLICATION_CREDENTIALS to: {SERVICE_ACCOUNT_PATH}")
    
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = SERVICE_ACCOUNT_PATH
    
    print(f"[DOCAI-CLIENT] Environment variable set")
    print(f"[DOCAI-CLIENT] Creating ClientOptions with endpoint: {LOCATION}-documentai.googleapis.com")

    opts = ClientOptions(
        api_endpoint=f"{LOCATION}-documentai.googleapis.com"
    )
    
    print(f"[DOCAI-CLIENT] ClientOptions created: {opts}")
    print(f"[DOCAI-CLIENT] Creating DocumentProcessorServiceClient...")

    client = documentai.DocumentProcessorServiceClient(
        client_options=opts
    )
    
    print(f"[DOCAI-CLIENT] ✅ Client created successfully: {type(client)}")
    print("---------- DOCAI.PY: get_client() COMPLETED ----------\n")
    
    return client


# ----------------------------
# PROCESS DOCUMENT
# ----------------------------

def process_document(file_bytes: bytes, mime_type: str):
    print("\n========== DOCAI.PY: process_document() STARTED ==========")
    print(f"[DOCAI-PROCESS] File size: {len(file_bytes)} bytes")
    print(f"[DOCAI-PROCESS] MIME type: {mime_type}")

    print(f"[DOCAI-PROCESS] Calling get_client()...")
    client = get_client()
    print(f"[DOCAI-PROCESS] Client obtained")

    print(f"[DOCAI-PROCESS] Building processor path...")
    print(f"[DOCAI-PROCESS] - PROJECT_ID: {PROJECT_ID}")
    print(f"[DOCAI-PROCESS] - LOCATION: {LOCATION}")
    print(f"[DOCAI-PROCESS] - PROCESSOR_ID: {PROCESSOR_ID}")
    
    name = client.processor_path(
        PROJECT_ID,
        LOCATION,
        PROCESSOR_ID
    )
    
    print(f"[DOCAI-PROCESS] Processor path: {name}")

    print(f"[DOCAI-PROCESS] Creating RawDocument...")
    raw_document = documentai.RawDocument(
        content=file_bytes,
        mime_type=mime_type
    )
    print(f"[DOCAI-PROCESS] RawDocument created: {type(raw_document)}")

    print(f"[DOCAI-PROCESS] Creating ProcessRequest...")
    request = documentai.ProcessRequest(
        name=name,
        raw_document=raw_document
    )
    print(f"[DOCAI-PROCESS] ProcessRequest created: {type(request)}")

    print(f"[DOCAI-PROCESS] 🚀 Sending request to Document AI API...")
    result = client.process_document(request=request)
    print(f"[DOCAI-PROCESS] ✅ Response received from Document AI")
    print(f"[DOCAI-PROCESS] Result type: {type(result)}")
    
    document = result.document
    print(f"[DOCAI-PROCESS] Document type: {type(document)}")
    print(f"[DOCAI-PROCESS] Document text length: {len(document.text)} characters")
    print(f"[DOCAI-PROCESS] Document text preview (first 200 chars):\n{document.text[:200]}")
    
    # Try to access entities
    try:
        entities_count = len(document.entities) if hasattr(document, 'entities') else 0
        print(f"[DOCAI-PROCESS] Number of entities: {entities_count}")
    except:
        print(f"[DOCAI-PROCESS] Could not count entities")
    
    print("========== DOCAI.PY: process_document() COMPLETED ==========\n")
    
    return document