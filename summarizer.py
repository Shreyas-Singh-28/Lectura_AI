# summarizer.py
from transformers import pipeline
import os
from typing import Optional

class ContentSummarizer:
    def __init__(self):
        # Initialize the summarization pipeline
        self.summarizer = pipeline(
            "summarization",
            model="facebook/bart-large-cnn",
            framework="pt"
        )
    
    def summarize_text(self, text: str, max_length: int = 150, min_length: int = 30) -> Optional[str]:
        """Summarize the given text using BART model"""
        try:
            if not text.strip():
                return None
                
            # Split text into chunks of 1024 tokens (model limit)
            chunks = self._chunk_text(text)
            summaries = []
            
            for chunk in chunks:
                summary = self.summarizer(
                    chunk,
                    max_length=max_length,
                    min_length=min_length,
                    do_sample=False
                )
                summaries.append(summary[0]['summary_text'])
            
            return " ".join(summaries)
        except Exception as e:
            print(f"Summarization error: {e}")
            return None
    
    def _chunk_text(self, text: str, chunk_size: int = 1000) -> list:
        """Split text into manageable chunks for the model"""
        words = text.split()
        chunks = []
        
        for i in range(0, len(words), chunk_size):
            chunk = " ".join(words[i:i+chunk_size])
            chunks.append(chunk)
        
        return chunks

def summarize_transcription(upload_folder: str = "uploads") -> Optional[str]:
    """Main function to summarize the transcription.txt file"""
    transcription_path = os.path.join(upload_folder, "transcription.txt")
    summary_path = os.path.join(upload_folder, "summary.txt")
    
    if not os.path.exists(transcription_path):
        return None
    
    try:
        with open(transcription_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        summarizer = ContentSummarizer()
        summary = summarizer.summarize_text(content)
        
        if summary:
            # Save the summary for future use
            with open(summary_path, "w", encoding="utf-8") as f:
                f.write(summary)
            
            return summary
        
        return None
    except Exception as e:
        print(f"Error summarizing transcription: {e}")
        return None