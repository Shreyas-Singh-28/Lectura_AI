import sys
import os
from dotenv import load_dotenv

load_dotenv()

def transcribe_audio(file_path):
    import whisper
    model = whisper.load_model("base")
    result = model.transcribe(file_path)
    return result["text"]

def extract_text_pdf(file_path):
    try:
        import PyPDF2
        text = ""
        with open(file_path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            for page in reader.pages:
                text += page.extract_text() + "\n"
        return text.strip()
    except Exception as e:
        raise Exception(f"PDF processing failed: {str(e)}")

def extract_text_docx(file_path):
    try:
        import docx
        doc = docx.Document(file_path)
        return "\n".join([para.text for para in doc.paragraphs])
    except Exception as e:
        raise Exception(f"DOCX processing failed: {str(e)}")

def extract_text_txt(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        raise Exception(f"TXT processing failed: {str(e)}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Error: Provide file path", file=sys.stderr)
        sys.exit(1)

    file_path = sys.argv[1]
    ext = os.path.splitext(file_path)[1].lower()

    try:
        if ext == '.pdf':
            print(extract_text_pdf(file_path))
        elif ext == '.docx':
            print(extract_text_docx(file_path))
        elif ext == '.txt':
            print(extract_text_txt(file_path))
        else:
            print(transcribe_audio(file_path))
    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)