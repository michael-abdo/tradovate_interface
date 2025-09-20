#!/usr/bin/env python3
"""
Extract text from Databento PDF document
"""

import PyPDF2
import sys

def extract_pdf_text(pdf_path):
    """Extract text from PDF file"""
    try:
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            text = ""
            
            print(f"📄 PDF has {len(pdf_reader.pages)} pages")
            
            for page_num in range(len(pdf_reader.pages)):
                page = pdf_reader.pages[page_num]
                page_text = page.extract_text()
                text += f"\n--- PAGE {page_num + 1} ---\n"
                text += page_text
            
            return text
            
    except Exception as e:
        print(f"Error reading PDF: {e}")
        return None

def main():
    pdf_path = "/Users/Mike/Downloads/Databento Support for Nasdaq-100 Futures and Options Data.pdf"
    
    print("🔍 EXTRACTING DATABENTO PDF CONTENT")
    print("="*60)
    
    text = extract_pdf_text(pdf_path)
    
    if text:
        # Save extracted text
        with open("databento_nq_support_document.txt", "w", encoding="utf-8") as f:
            f.write(text)
        
        print("✅ Text extracted successfully!")
        print(f"📝 Saved to: databento_nq_support_document.txt")
        
        # Print key sections
        print("\n" + "="*60)
        print("📋 KEY CONTENT PREVIEW")
        print("="*60)
        
        # Show first 2000 characters
        preview = text[:2000]
        print(preview)
        
        if len(text) > 2000:
            print(f"\n... (showing first 2000 of {len(text)} total characters)")
    
    else:
        print("❌ Failed to extract text from PDF")

if __name__ == "__main__":
    main()