import os
from openai import OpenAI
from dotenv import load_dotenv
import pandas as pd
import json
import time
from document_processor import get_relevant_documents, get_all_documents, excel_json_data

# Store conversation history
conversation_history = []

# Load environment variables
load_dotenv()

# Initialize OpenAI client
try:
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    print(f"OpenAI client initialized successfully")
except Exception as e:
    print(f"Error initializing OpenAI client: {e}")
    client = None

def _debug_data(data):
    """
    Utility to debug data by writing to a temp file
    """
    try:
        with open("debug_data.json", "w", encoding="utf-8") as f:
            json.dump({"data": data, "timestamp": time.time()}, f, ensure_ascii=False, indent=2)
        print(f"Debug data written to debug_data.json")
    except Exception as e:
        print(f"Error writing debug data: {e}")

def _extract_file_content(file_path):
    """
    Extract content from a file directly if needed
    """
    print(f"Trying to extract content directly from {file_path}")
    try:
        from document_processor import process_excel, process_docx, process_pdf, process_txt
        
        if file_path.endswith('.xlsx') or file_path.endswith('.xls'):
            return process_excel(file_path)
        elif file_path.endswith('.docx'):
            return process_docx(file_path)
        elif file_path.endswith('.pdf'):
            return process_pdf(file_path)
        elif file_path.endswith('.txt'):
            return process_txt(file_path)
        else:
            print(f"Unsupported file type: {file_path}")
            return None
    except Exception as e:
        print(f"Error extracting file content: {e}")
        import traceback
        traceback.print_exc()
        return None

def _find_uploaded_files():
    """
    Find all uploaded files in the uploads directory
    """
    uploads_dir = "uploads"
    files = []
    try:
        for filename in os.listdir(uploads_dir):
            file_path = os.path.join(uploads_dir, filename)
            if os.path.isfile(file_path):
                files.append(file_path)
        return files
    except Exception as e:
        print(f"Error finding uploaded files: {e}")
        return []

def get_answer_from_docs(query):
    """
    Get an answer to a query from the uploaded documents using OpenAI
    """
    print(f"\n\n==== Processing chat query: {query} ====")
    
    # Import here to avoid circular imports
    from document_processor import get_relevant_documents, get_all_documents, is_document_store_empty
    
    # Check if document store is empty
    if is_document_store_empty():
        print("Document store is empty, checking for files in uploads folder")
        # Try direct file access since document store is empty
        uploaded_files = _find_uploaded_files()
        print(f"Found {len(uploaded_files)} uploaded files: {uploaded_files}")
        
        if not uploaded_files:
            return "I don't have any information about that. Please upload documents first."
        
        # Process the most recent file if available
        if uploaded_files:
            # Sort by modification time (most recent first)
            uploaded_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
            latest_file = uploaded_files[0]
            print(f"Processing most recent file: {latest_file}")
            
            # Extract content
            content = _extract_file_content(latest_file)
            if content:
                print(f"Successfully extracted content from {latest_file}")
                relevant_docs = [content]
            else:
                return f"I couldn't extract content from the uploaded file. Please try uploading again or use a different file format."
        else:
            return "I don't have any information about that. Please upload documents first."
    else:
        # Document store has content, retrieve documents
        print("Fetching documents from document store...")
        relevant_docs = get_relevant_documents(query)
        
        print(f"Found {len(relevant_docs)} relevant documents")
        
        # If no relevant docs, get all docs
        if not relevant_docs:
            print("No relevant documents found, fetching all...")
            relevant_docs = get_all_documents(limit=10)
            print(f"Retrieved {len(relevant_docs)} total documents from store")
    
    # Combine relevant documents (limit context size to avoid token limits)
    max_context_length = 15000  # Limit context to ~15k characters
    context = ""
    
    # Add documents up to max length
    for doc in relevant_docs:
        if len(context) + len(doc) <= max_context_length:
            if context:
                context += "\n\n" + doc
            else:
                context = doc
        else:
            # If adding this doc would exceed limit, stop
            break
    
    print(f"Final context length: {len(context)} characters")
    
    # Save context for debugging
    _debug_data({"query": query, "context": context[:5000]})
    
    # Detect if we're dealing with Excel data
    is_excel_data = 'EXCEL FILE SUMMARY' in context or 'SHEET:' in context
    
    # Check if we have JSON data from Excel
    has_excel_json = bool(excel_json_data)
    
    # Create messages for OpenAI based on document type
    if is_excel_data and has_excel_json:
        # Use JSON format for Excel data
        print(f"Using Excel JSON data for analysis with GPT-4.1")
        
        # Create a more concise representation of the JSON data if it's too large
        excel_json_str = json.dumps(excel_json_data, indent=2)
        if len(excel_json_str) > 12000:  # Limit size for API
            # Create a summary of the data structure
            excel_summary = {}
            for sheet_name, records in excel_json_data.items():
                # Include only first 5 records and metadata
                sample = records[:5] if len(records) > 5 else records
                excel_summary[sheet_name] = {
                    "sample_records": sample,
                    "total_records": len(records),
                    "columns": list(sample[0].keys()) if sample else []
                }
            excel_json_str = json.dumps(excel_summary, indent=2)
        
        prompt = f"""
        Analyze this Excel data in JSON format and answer the user's question.
        The data contains multiple sheets with their records in JSON format.
        Perform detailed data analysis including finding patterns, analyzing numerical values,
        identifying relationships, and calculating statistics as needed.
        
        IMPORTANT: If the user's question is in Indonesian language, respond in Indonesian language.
        If the question is in English, respond in English. Always match the language used in the question.
        
        EXCEL DATA (JSON FORMAT):
        {excel_json_str}
        
        USER QUESTION:
        {query}
        """
    elif is_excel_data:
        # Use text format for Excel data
        prompt = f"""
        Based on the following Excel data, please analyze and answer the question.
        This is structured data from an Excel spreadsheet with statistics and insights included.
        Perform data analysis on the Excel content, including:
        - Finding patterns in the data
        - Analyzing numerical values and statistics
        - Drawing insights from the structured data
        - Identifying relationships between columns where possible
        
        IMPORTANT: If the user's question is in Indonesian language, respond in Indonesian language.
        If the question is in English, respond in English. Always match the language used in the question.
        
        EXCEL DATA:
        {context}
        
        USER QUESTION:
        {query}
        """
    else:
        prompt = f"""
        Based on the following information from uploaded documents, please answer the question.
        Analyze the content carefully and provide a detailed response.
        If the information doesn't contain an answer to the question, explain what information is available.
        
        IMPORTANT: If the user's question is in Indonesian language, respond in Indonesian language.
        If the question is in English, respond in English. Always match the language used in the question.
        
        DOCUMENT CONTENT:
        {context}
        
        USER QUESTION:
        {query}
        """
    
    # Add current query to conversation history
    global conversation_history
    
    try:
        # Prepare messages for OpenAI API
        messages = []
        
        # Determine system message based on document type
        if is_excel_data:
            system_content = """
            You are a data analyst specializing in Excel data analysis. Your strengths include:
            - Analyzing structured data from Excel files
            - Identifying patterns and trends in numerical data
            - Calculating and interpreting statistics
            - Providing insights about relationships between data elements
            - Explaining data in a clear, concise manner
            
            Maintain context from the conversation history when appropriate.
            
            IMPORTANT: When a user asks a question in Indonesian language, you MUST respond in Indonesian language as well.
            Always match the language of your response to the language used in the question.
            """
        else:
            system_content = """
            You are a helpful assistant that analyzes document content and provides detailed, accurate answers 
            based on the information available. Always analyze the provided document content thoroughly before responding.
            
            Maintain context from the conversation history when appropriate.
            
            IMPORTANT: When a user asks a question in Indonesian language, you MUST respond in Indonesian language as well.
            Always match the language of your response to the language used in the question.
            """
        
        # Add system message
        messages.append({"role": "system", "content": system_content})
        
        # Add conversation history (up to 5 most recent exchanges)
        history_limit = min(5, len(conversation_history))
        for msg in conversation_history[-history_limit:]:
            messages.append(msg)
            
        # Add current prompt with context
        messages.append({"role": "user", "content": prompt})
        
        print(f"Sending {len(messages)} messages to OpenAI including history")
            
        # Use gpt-4-turbo (latest version of GPT-4) when working with Excel JSON data
        if is_excel_data and has_excel_json:
            model_name = "gpt-5"  # The latest GPT-4 model
        else:
            model_name = "gpt-5"
            
        print(f"Using model: {model_name}")
        
        response = client.chat.completions.create(
            model=model_name,
            messages=messages
        )
        
        # Extract answer from response
        answer = response.choices[0].message.content.strip()
        print(f"OpenAI response received, length: {len(answer)}")
        
        # Save to conversation history
        conversation_history.append({"role": "user", "content": query})
        conversation_history.append({"role": "assistant", "content": answer})
        
        # Limit history size to prevent context overflow
        if len(conversation_history) > 20:  # Keep last 10 exchanges (20 messages)
            conversation_history = conversation_history[-20:]
            
        print(f"Conversation history updated, now has {len(conversation_history)} messages")
        
        return answer
        
    except Exception as e:
        print(f"Error calling OpenAI API: {str(e)}")
        return f"Sorry, I encountered an error processing your question: {str(e)}"

