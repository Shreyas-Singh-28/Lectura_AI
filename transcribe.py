import sys
import os
import subprocess
import tempfile
import shutil
from dotenv import load_dotenv

load_dotenv()

def check_ffmpeg():
    """Check if ffmpeg is available in the system path"""
    if shutil.which("ffmpeg") is None:
        raise Exception("ffmpeg is not installed or not found in PATH. Please install ffmpeg and try again.")

def convert_to_wav(input_path, temp_dir):
    """Convert media file to WAV format using FFmpeg"""
    output_path = os.path.join(temp_dir, "converted_audio.wav")
    
    command = [
        "ffmpeg",
        "-i", input_path,
        "-ar", "16000",  # Set audio sample rate to 16kHz
        "-ac", "1",      # Set audio channels to mono
        "-y",            # Overwrite output file without asking
        output_path
    ]
    
    try:
        subprocess.run(command, check=True, capture_output=True)
    except subprocess.CalledProcessError as e:
        error_message = f"FFmpeg conversion failed: {e.stderr.decode()}"
        raise Exception(error_message)
    
    return output_path

def transcribe_audio(file_path):
    """Transcribe audio using Whisper"""
    import whisper
    model = whisper.load_model("base")
    result = model.transcribe(file_path)
    return result["text"]

def extract_text_pdf(file_path):
    """Extract text from PDF files"""
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
    """Extract text from DOCX files"""
    try:
        import docx
        doc = docx.Document(file_path)
        return "\n".join([para.text for para in doc.paragraphs])
    except Exception as e:
        raise Exception(f"DOCX processing failed: {str(e)}")

def extract_text_txt(file_path):
    """Extract text from TXT files"""
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
        elif ext in ('.mp3', '.mp4'):
            check_ffmpeg()
            temp_dir = tempfile.mkdtemp()
            try:
                wav_path = convert_to_wav(file_path, temp_dir)
                print(transcribe_audio(wav_path))
            finally:
                shutil.rmtree(temp_dir)
        else:
            print(transcribe_audio(file_path))
    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)