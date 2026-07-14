import base64
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
from polibot.ingestion.captioning import caption_image
from polibot.ingestion.chunking import read_pdf
import fitz  # PyMuPDF

def generate_sample_image() -> bytes:
    # Create an image with text indicating a math concept
    img = Image.new('RGB', (400, 200), color=(73, 109, 137))
    d = ImageDraw.Draw(img)
    d.text((20, 80), "Graph of f(x) = x^2", fill=(255, 255, 0))
    d.text((20, 110), "Shows a parabola opening upwards", fill=(255, 255, 255))
    
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    return buffered.getvalue()

def generate_sample_pdf(path: str):
    # Create a simple PDF using PyMuPDF
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 50), "PoliBot RAG Architecture: Multimodal Parsing")
    page.insert_text((50, 80), "This slide contains purely textual information.")
    
    # Add an image to the PDF
    img_bytes = generate_sample_image()
    rect = fitz.Rect(50, 150, 250, 250)
    page.insert_image(rect, stream=img_bytes)
    
    doc.save(path)
    doc.close()

def main():
    print("--- Running PDF Parsing and Vision / Image Captioning Demonstration ---")
    
    # 1. Test Vision / Captioning on raw image
    print("\n[Testing Vision Model (gemma4:e2b) on Raw Image]")
    img_bytes = generate_sample_image()
    caption = caption_image(img_bytes)
    print("Extracted Image Caption:")
    print(f"  {caption}")
    
    # 2. Test PDF text and image extraction
    print("\n[Testing PDF Pipeline (Text Extraction + Image Extraction)]")
    pdf_path = "/tmp/demo_multimodal.pdf"
    generate_sample_pdf(pdf_path)
    
    pages = read_pdf(pdf_path)
    print(f"Parsed {len(pages)} page(s) from PDF.")
    print(f"Page 1 Text Content:")
    print(f"  {pages[0].text.strip()}")
    print(f"Page 1 Extracted Images Count: {len(pages[0].images)}")
    
    if pages[0].images:
        print("\n[Captioning Extracted PDF Image via Vision Model]")
        pdf_caption = caption_image(pages[0].images[0])
        print(f"  {pdf_caption}")

if __name__ == "__main__":
    main()
