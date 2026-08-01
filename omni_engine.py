import os
import time
import json
import csv
import logging
import fitz  # PyMuPDF
import docx  # python-docx
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from openai import OpenAI
from dotenv import load_dotenv
load_dotenv()

# --- ENTERPRISE SYSTEM CONFIGURATION ---
INPUT_DIR = "./input_payloads"
JSON_LEDGER = "commercial_ledger.json"
CSV_LEDGER = "commercial_ledger.csv"
CHUNK_SIZE = 50

# Enterprise Logging Protocol (Replaces basic terminal prints for error tracking)
logging.basicConfig(
    filename='system_execution.log', 
    level=logging.INFO, 
    format='%(asctime)s - [OMNI CORE] - %(levelname)s - %(message)s'
)

# [INSERT YOUR NEWLY GENERATED OPENROUTER API KEY HERE]
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY")
)

class OmniIngestionCore(FileSystemEventHandler):
    """
    Object-Oriented Core Engine for versatile payload ingestion.
    Routes file formats to dedicated private parsing methods.
    """
    def on_created(self, event):
        if event.is_directory:
            return
            
        file_path = event.src_path.lower()
        time.sleep(2)  # OS lock buffer for large file transfers
        
        try:
            if file_path.endswith(".pdf"):
                logging.info(f"PDF Payload Detected: {event.src_path}")
                self._parse_pdf(event.src_path)
            elif file_path.endswith(".txt"):
                logging.info(f"TXT Payload Detected: {event.src_path}")
                self._parse_txt(event.src_path)
            elif file_path.endswith(".docx"):
                logging.info(f"DOCX Payload Detected: {event.src_path}")
                self._parse_docx(event.src_path)
            else:
                logging.warning(f"Unsupported Payload Format: {event.src_path}")
        except Exception as e:
            logging.error(f"Critical Ingestion Failure on {event.src_path}: {e}")

    def _parse_txt(self, file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            text = f.read()
        self._invoke_shadow_matrix(text, os.path.basename(file_path))

    def _parse_docx(self, file_path):
        doc = docx.Document(file_path)
        full_text = [para.text for para in doc.paragraphs]
        raw_text = '\n'.join(full_text)
        self._invoke_shadow_matrix(raw_text, os.path.basename(file_path))

    def _parse_pdf(self, file_path):
        doc = fitz.open(file_path)
        total_pages = doc.page_count
        logging.info(f"PDF Geometry verified. Total Pages: {total_pages}. Commencing Chunking.")
        
        for start in range(0, total_pages, CHUNK_SIZE):
            end = min(start + CHUNK_SIZE - 1, total_pages - 1)
            chunk_text = ""
            
            for page_num in range(start, end + 1):
                page = doc.load_page(page_num)
                chunk_text += page.get_text("text") + " "
            
            # --- SYSTEM GATE: HUMAN IN THE LOOP ---
            print(f"\n[SYSTEM GATE] Chunk {start}-{end} of {os.path.basename(file_path)} prepared.")
            permission = input("Does the Monarch grant permission to execute API extraction? (Y/N): ")
            
            if permission.upper() == 'Y':
                self._invoke_shadow_matrix(chunk_text, f"{os.path.basename(file_path)} (Pgs {start}-{end})")
            else:
                logging.warning(f"Execution aborted by Monarch for chunk {start}-{end}.")
            
            time.sleep(1)
        doc.close()

    def _invoke_shadow_matrix(self, raw_data, source_ref):
        system_prompt = """You are an elite data extraction core. Extract client name, contact email, transaction date, and total billed. Output STRICTLY as a JSON array of objects with keys: ClientName, ContactEmail, TransactionDate, CalculatedTotal. No markdown. No conversational text."""
        
        logging.info(f"Invoking Shadow Matrix for {source_ref}...")
        try:
            response = client.chat.completions.create(
                model="openrouter/auto", 
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": raw_data}
                ]
            )
            raw_output = response.choices[0].message.content
            self._purify_and_slice(raw_output, source_ref)
        except Exception as api_error:
            logging.error(f"Neural Bridge Failure: {api_error}")

    def _purify_and_slice(self, raw_output, source_ref):
        start_idx = raw_output.find('[')
        end_idx = raw_output.rfind(']') + 1
        
        if start_idx != -1 and end_idx != 0:
            clean_json = raw_output[start_idx:end_idx]
            try:
                data_list = json.loads(clean_json)
                for item in data_list:
                    item["SourceReference"] = source_ref
                
                self._write_to_ledgers(data_list)
                logging.info(f"Extraction successful. {len(data_list)} records mapped for {source_ref}.")
                print(f"[SUCCESS] Corporate payload mapped and secured for {source_ref}.")
            except json.JSONDecodeError:
                logging.error(f"Shadow Hallucination: Failed to parse JSON string -> {clean_json}")
        else:
            logging.error(f"Shadow Hallucination: No strict JSON array detected. Output -> {raw_output}")

    def _write_to_ledgers(self, data_list):
        if not data_list: return
        
        # JSON Ledger Appending
        existing_data = []
        if os.path.exists(JSON_LEDGER):
            with open(JSON_LEDGER, 'r') as f:
                try: existing_data = json.load(f)
                except: pass
        existing_data.extend(data_list)
        with open(JSON_LEDGER, 'w') as f:
            json.dump(existing_data, f, indent=4)
        
        # CSV Ledger Appending
        file_exists = os.path.isfile(CSV_LEDGER)
        with open(CSV_LEDGER, 'a', newline='', encoding='utf-8') as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=data_list[0].keys())
            if not file_exists:
                writer.writeheader()
            writer.writerows(data_list)

def ignite_enterprise_core():
    if not os.path.exists(INPUT_DIR):
        os.makedirs(INPUT_DIR)
        
    event_handler = OmniIngestionCore()
    observer = Observer()
    observer.schedule(event_handler, INPUT_DIR, recursive=False)
    observer.start()
    
    print("\n[OMNI ENGINE V4.0 - ENTERPRISE EDITION ACTIVE]")
    print(f"Monitoring '{INPUT_DIR}' for PDF/TXT/DOCX payloads...")
    print("Background execution logging routed to 'system_execution.log'.\n")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        print("\n[OMNI ENGINE OFFLINE]")
    observer.join()

if __name__ == "__main__":
    ignite_enterprise_core()