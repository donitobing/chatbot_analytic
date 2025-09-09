import os
import docx
import pandas as pd
import pdfplumber
import chromadb
from langchain.text_splitter import RecursiveCharacterTextSplitter

# Instead of ChromaDB, we'll use a simple in-memory document store
import os
from datetime import datetime

# Global document store - simple dictionary to hold documents
document_store = {}

# Document metadata store
document_metadata = {}

# Store Excel data in JSON format for direct API access
excel_json_data = {}

print("Using simple in-memory document store instead of ChromaDB")

# Function to clear document store
def clear_document_store():
    global document_store, document_metadata
    document_store = {}
    document_metadata = {}
    print("Document store cleared")
    return True

# Function to add document to store
def add_document(doc_id, content, metadata=None):
    global document_store, document_metadata
    document_store[doc_id] = content
    document_metadata[doc_id] = {
        "timestamp": datetime.now().isoformat(),
        "metadata": metadata or {}
    }
    return True

# Function to get all documents
def get_documents():
    return document_store

# Function to check if document store is empty
def is_document_store_empty():
    return len(document_store) == 0

def process_document(file_path):
    """Process document based on file extension and store in vector DB"""
    print(f"Processing document: {file_path}")
    _, file_extension = os.path.splitext(file_path)
    file_extension = file_extension.lower()
    
    # Check if file exists
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return False
    
    print(f"Detected file type: {file_extension}")
    
    try:
        # Extract text based on file type
        if file_extension == '.docx':
            print("Processing Word document...")
            text = process_docx(file_path)
        elif file_extension == '.xlsx' or file_extension == '.xls':
            print("Processing Excel document...")
            text = process_excel(file_path)
        elif file_extension == '.pdf':
            print("Processing PDF document...")
            text = process_pdf(file_path)
        elif file_extension == '.txt':
            print("Processing text document...")
            text = process_txt(file_path)
        else:
            print(f"Unsupported file type: {file_extension}")
            raise ValueError(f"Unsupported file type: {file_extension}")
        
        print(f"Successfully extracted text, length: {len(text)}")
        
        # Split text into chunks for vector storage
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=100,
            length_function=len,
        )
        chunks = text_splitter.split_text(text)
        print(f"Split into {len(chunks)} chunks")
        
        # Clear existing documents when uploading a new one
        clear_document_store()
        
        # Store document in memory
        doc_id = os.path.basename(file_path)
        
        # Store the text directly
        if text and len(text) > 0:
            print(f"Storing document: {doc_id} (length: {len(text)})")

            add_document(doc_id, text, {"source": file_path, "type": file_extension})
            print(f"Successfully stored document in memory")

        else:
            print("Warning: No text to store from document")

        
        # If we have chunks, store them as well for more detailed access
        if chunks and len(chunks) > 0:
            print(f"Storing {len(chunks)} chunks from document")

            for i, chunk in enumerate(chunks):
                chunk_id = f"{doc_id}_chunk_{i}"
                add_document(chunk_id, chunk, {
                    "source": file_path,
                    "chunk_id": i,
                    "total_chunks": len(chunks),
                    "parent_doc": doc_id
                })
        
        # Verify storage was successful
        doc_count = len(document_store)
        print(f"Document store now has {doc_count} documents/chunks")

            
        return True
    except Exception as e:
        print(f"Error processing document: {e}")
        import traceback
        traceback.print_exc()
        return False

def process_docx(file_path):
    """Extract text from DOCX file"""
    doc = docx.Document(file_path)
    full_text = []
    for para in doc.paragraphs:
        full_text.append(para.text)
    return '\n'.join(full_text)

def process_excel(file_path):
    """Extract structured data from Excel file and convert to JSON format"""
    print(f"Processing Excel file: {file_path}")
    try:
        # Read all sheets in the Excel file
        df = pd.read_excel(file_path, sheet_name=None)
        
        # Store the original data in JSON format for direct API access
        excel_data_json = {}
        for sheet_name, sheet_df in df.items():
            # Convert DataFrame to records format (list of dictionaries)
            excel_data_json[sheet_name] = sheet_df.to_dict(orient='records')
        
        # Store the JSON data for later use
        global excel_json_data
        excel_json_data = excel_data_json
        
        structured_texts = []
        print(f"Excel file has {len(df)} sheets: {list(df.keys())}")
        
        # First add a summary section
        summary = [f"EXCEL FILE SUMMARY: {os.path.basename(file_path)}", 
                  f"Total sheets: {len(df)}", 
                  f"Sheet names: {', '.join(list(df.keys()))}",
                  ""]
        structured_texts.extend(summary)
        
        # Process each sheet
        for sheet_name, sheet_df in df.items():
            print(f"Processing sheet: {sheet_name} with {len(sheet_df)} rows and {len(sheet_df.columns)} columns")
            
            # Add sheet header with statistical summary
            sheet_header = [f"SHEET: {sheet_name}",
                          f"Rows: {len(sheet_df)}", 
                          f"Columns: {len(sheet_df.columns)}",
                          f"Column names: {', '.join(sheet_df.columns.astype(str))}",
                          ""]
            
            # Enhanced numerical analysis
            try:
                # Convert column names to lowercase for case-insensitive matching
                lower_cols = {col.lower(): col for col in sheet_df.columns}
                
                # Try to identify profit or revenue columns
                profit_keywords = ['profit', 'laba', 'keuntungan', 'revenue', 'pendapatan', 'income']
                profit_cols = []
                for keyword in profit_keywords:
                    matching_cols = [lower_cols[col] for col in lower_cols if keyword in col.lower()]
                    profit_cols.extend(matching_cols)
                
                if profit_cols:
                    sheet_header.append("PROFIT/REVENUE ANALYSIS:")
                    for col in profit_cols:
                        try:
                            # Get top profit entries
                            top_n = 5  # Number of top entries to show
                            top_profit = sheet_df.nlargest(top_n, col)
                            
                            sheet_header.append(f"Top {top_n} highest {col}:")
                            for i, (idx, row) in enumerate(top_profit.iterrows(), 1):
                                # Try to find identifying columns like name, product, etc.
                                id_cols = [c for c in sheet_df.columns if any(k in c.lower() for k in ['name', 'nama', 'product', 'produk', 'item', 'description', 'deskripsi', 'id'])]
                                
                                if id_cols:
                                    identifiers = [f"{c}: {row[c]}" for c in id_cols if pd.notna(row[c])]
                                    item_desc = ", ".join(identifiers)
                                else:
                                    # Use row index as identifier
                                    item_desc = f"Row {idx+1}"
                                    
                                sheet_header.append(f"  {i}. {item_desc} = {row[col]}")
                            sheet_header.append("")
                            
                            # Calculate profit distribution
                            sheet_header.append(f"{col} distribution:")
                            quartiles = sheet_df[col].quantile([0.25, 0.5, 0.75]).to_dict()
                            sheet_header.append(f"  25% of values are below: {quartiles[0.25]}")
                            sheet_header.append(f"  Median value: {quartiles[0.5]}")
                            sheet_header.append(f"  75% of values are above: {quartiles[0.75]}")
                            sheet_header.append("")
                        except Exception as e:
                            print(f"Error analyzing profit column {col}: {e}")
            except Exception as e:
                print(f"Error in enhanced profit analysis: {e}")
            
            # Add statistical summaries for numerical columns
            numerical_cols = sheet_df.select_dtypes(include=['number']).columns
            if len(numerical_cols) > 0:
                sheet_header.append("NUMERICAL COLUMN STATISTICS:")
                for col in numerical_cols:
                    try:
                        stats = f"Column '{col}': Min={sheet_df[col].min()}, Max={sheet_df[col].max()}, Mean={sheet_df[col].mean():.2f}, Sum={sheet_df[col].sum()}"
                        sheet_header.append(stats)
                    except Exception as e:
                        print(f"Error calculating stats for {col}: {e}")
                sheet_header.append("")
            
            structured_texts.extend(sheet_header)
            
            # Process data in chunks to maintain structure
            if len(sheet_df) > 0:
                structured_texts.append("DATA:")
                
                # Format as a structured table - first the headers
                header_row = " | ".join([f"{col}" for col in sheet_df.columns])
                structured_texts.append(header_row)
                structured_texts.append("-" * len(header_row))  # Separator line
                
                # Then row data in a structured format
                for i, row in sheet_df.iterrows():
                    if i < 100:  # Limit rows to prevent massive texts
                        row_str = " | ".join([f"{val}" for val in row.values])
                        structured_texts.append(row_str)
                    else:
                        structured_texts.append(f"... (Showing first 100 of {len(sheet_df)} rows)")
                        break
                
                structured_texts.append("")  # Blank line after data
            
            # Try to identify key insights if possible
            structured_texts.append("POTENTIAL INSIGHTS:")
            
            # Enhanced correlation analysis between columns
            try:
                # Calculate correlations between numerical columns
                if len(numerical_cols) > 1:
                    corr_matrix = sheet_df[numerical_cols].corr()
                    # Find strong correlations (absolute value > 0.7)
                    strong_correlations = []
                    for i in range(len(numerical_cols)):
                        for j in range(i+1, len(numerical_cols)):
                            col1, col2 = numerical_cols[i], numerical_cols[j]
                            corr_val = corr_matrix.loc[col1, col2]
                            if abs(corr_val) > 0.7:  # Strong correlation threshold
                                relation = "positively" if corr_val > 0 else "negatively"
                                strong_correlations.append(
                                    f"- Strong {relation} correlation ({corr_val:.2f}) between '{col1}' and '{col2}'"
                                )
                    
                    if strong_correlations:
                        structured_texts.append("CORRELATIONS:")
                        structured_texts.extend(strong_correlations)
                        structured_texts.append("")
            except Exception as e:
                print(f"Error analyzing correlations: {e}")
                
            # Check for dates to suggest time-series analysis
            date_cols = sheet_df.select_dtypes(include=['datetime64']).columns
            if len(date_cols) > 0:
                structured_texts.append(f"- Time series data detected in columns: {', '.join(date_cols)}")
                
                # Try to analyze trends over time if date and numeric columns exist
                if len(numerical_cols) > 0 and len(date_cols) > 0:
                    try:
                        date_col = date_cols[0]  # Use first date column
                        structured_texts.append(f"TREND ANALYSIS using date column: {date_col}")
                        
                        # Sort by date
                        sorted_df = sheet_df.sort_values(date_col)
                        
                        # Look at changes in numerical columns over time
                        for num_col in numerical_cols[:3]:  # Analyze up to 3 columns
                            try:
                                first_val = sorted_df[num_col].iloc[0]
                                last_val = sorted_df[num_col].iloc[-1]
                                change = last_val - first_val
                                pct_change = (change / first_val * 100) if first_val != 0 else float('inf')
                                
                                direction = "increased" if change > 0 else "decreased" if change < 0 else "remained the same"
                                
                                structured_texts.append(
                                    f"- '{num_col}' {direction} by {abs(change):.2f} ({abs(pct_change):.1f}%) from "
                                    f"{sorted_df[date_col].iloc[0]} to {sorted_df[date_col].iloc[-1]}"
                                )
                            except:
                                pass
                        structured_texts.append("")
                    except Exception as e:
                        print(f"Error in trend analysis: {e}")
            
            # Check for potential ID columns
            for col in sheet_df.columns:
                if 'id' in str(col).lower() or 'code' in str(col).lower():
                    unique_vals = sheet_df[col].nunique()
                    structured_texts.append(f"- Possible ID column: '{col}' with {unique_vals} unique values")
            
            structured_texts.append("")  # Blank line
        
        result = '\n'.join(structured_texts)
        print(f"Total extracted structured text length: {len(result)}")
        return result
    except Exception as e:
        print(f"Error in Excel processing: {e}")
        import traceback
        traceback.print_exc()
        return f"Error processing Excel file: {str(e)}"

def process_pdf(file_path):
    """Extract text from PDF file"""
    text = []
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            text.append(page.extract_text())
    return '\n\n'.join(text)

def process_txt(file_path):
    """Extract text from TXT file"""
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
        return file.read()

def get_all_documents(limit=None):
    """Get all documents from the in-memory document store"""
    global document_store
    
    try:
        print(f"Getting all documents from in-memory store")
        
        # Check if document store is empty
        if is_document_store_empty():
            print("Document store is empty")
            return []
        
        # Get all document contents
        all_docs = list(document_store.values())
        
        # Apply limit if specified
        if limit and len(all_docs) > limit:
            all_docs = all_docs[:limit]
            
        print(f"Returning {len(all_docs)} documents from document store")
        return all_docs
    except Exception as e:
        print(f"Error getting all documents: {e}")
        import traceback
        traceback.print_exc()
        return []

def get_relevant_documents(query, top_k=5):
    """Retrieve relevant documents for a query from in-memory store"""
    global document_store
    
    print(f"Searching for documents relevant to query: {query}")
    
    try:
        # Check if document store is empty
        if is_document_store_empty():
            print("Document store is empty")
            return []
            
        # Simple relevance: just return all documents
        # In a real implementation, you could add simple keyword matching here
        docs = list(document_store.values())
        
        print(f"Found {len(docs)} documents in store")
        
        # Return up to top_k documents
        return docs[:top_k] if top_k < len(docs) else docs
    except Exception as e:
        print(f"Error searching document store: {e}")
        import traceback
        traceback.print_exc()
        return []
