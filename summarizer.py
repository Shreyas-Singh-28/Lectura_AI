# summarizer.py
from transformers import pipeline
import os
import math
from typing import Optional

class ContentSummarizer:
    def __init__(self):
        # Initialize with model that has defined max length
        self.summarizer = pipeline(
            "summarization",
            model="facebook/bart-large-cnn",
            framework="pt"
        )
        self.model_max_length = 1024  # Specific to bart-large-cnn

    def summarize_text(self, text: str) -> Optional[str]:
        """Generate dynamic summary (~40% of original length) with safe handling"""
        try:
            if not text.strip():
                return None

            # Calculate target lengths safely
            word_count = len(text.split())
            if word_count < 80:
                return None  # Skip summarization for very short texts

            # Calculate dynamic lengths
            target_summary_length = max(60, math.floor(word_count * 0.4))
            chunk_size = self._calculate_chunk_size(word_count)

            # Split text into model-safe chunks
            chunks = self._chunk_text(text, chunk_size)
            if not chunks:
                return None

            summaries = []
            for chunk in chunks:
                chunk_word_count = len(chunk.split())
                if chunk_word_count < 40:  # Skip tiny chunks
                    continue

                # Calculate chunk-specific limits
                chunk_target = max(
                    40,
                    min(
                        math.floor(chunk_word_count * 0.4),
                        self.model_max_length - 60  # Leave room for generation
                    )
                )

                try:
                    summary = self.summarizer(
                        chunk,
                        max_length=chunk_target,
                        min_length=max(30, math.floor(chunk_target * 0.5)),
                        do_sample=False,
                        truncation=True
                    )
                    if summary and len(summary) > 0:
                        summaries.append(summary[0]['summary_text'])
                except Exception as chunk_error:
                    print(f"Chunk processing error: {chunk_error}")
                    continue

            if not summaries:
                return None

            full_summary = " ".join(summaries)
            return self._finalize_summary(full_summary, target_summary_length)

        except Exception as e:
            print(f"Summarization error: {e}")
            return None

    def _calculate_chunk_size(self, word_count: int) -> int:
        """Determine safe chunk size based on input length"""
        if word_count <= 1000:
            return 800  # Single chunk
        return 600  # Smaller chunks for longer texts

    def _chunk_text(self, text: str, chunk_size: int) -> list:
        """Split text into safe chunks with overlap prevention"""
        words = text.split()
        if len(words) <= chunk_size:
            return [" ".join(words)]

        chunks = []
        for i in range(0, len(words), chunk_size):
            chunk = " ".join(words[i:i+chunk_size])
            # Prevent empty chunks
            if chunk.strip():
                chunks.append(chunk)
        return chunks

    def _finalize_summary(self, summary: str, target: int) -> str:
        """Ensure final summary quality and length"""
        summary_words = summary.split()
        if len(summary_words) > target * 1.2:  # If too long
            return " ".join(summary_words[:target])
        return summary

def summarize_transcription(upload_folder: str = "uploads") -> Optional[str]:
    """Main function with enhanced error handling"""
    try:
        transcription_path = os.path.join(upload_folder, "transcription.txt")
        if not os.path.exists(transcription_path):
            return None

        with open(transcription_path, "r", encoding="utf-8") as f:
            content = f.read().strip()

        if not content or len(content.split()) < 80:
            return "Content too short for meaningful summary"

        summarizer = ContentSummarizer()
        summary = summarizer.summarize_text(content)

        if summary:
            summary_path = os.path.join(upload_folder, "summary.txt")
            with open(summary_path, "w", encoding="utf-8") as f:
                f.write(f"Summary ({len(summary.split())} words):\n{summary}")
            return summary

        return "Summary generation failed - try with longer content"
    except Exception as e:
        print(f"Summarization failed: {e}")
        return None