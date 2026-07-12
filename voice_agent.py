#!/usr/bin/env python3
"""
Voice Agent: Talk to your documents

Usage:
    python voice_agent.py <document_path>
    python voice_agent.py  # will prompt for path

Example:
    python voice_agent.py data/policy.pdf
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

from app.loaders import load_document
from app.chunker import chunk_documents
from app.indexer import get_or_build_index
from app.qa_chain import query_document
from app.voice_io import record_from_mic, transcribe_audio, speak_response, has_mic_available
from app.web_fallback import search_web_for_answer

def main():
    load_dotenv()

    # Validate API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ Error: OPENAI_API_KEY not set in .env")
        sys.exit(1)

    # Get document path
    if len(sys.argv) > 1:
        doc_path = sys.argv[1]
    else:
        doc_path = input("Enter document path (PDF, DOCX, or TXT): ").strip()

    if not doc_path:
        print("❌ Document path required")
        sys.exit(1)

    # Load and prepare index
    try:
        print(f"\n📄 Loading document: {doc_path}")
        documents = load_document(doc_path)
        chunks = chunk_documents(documents)
        vector_store = get_or_build_index(doc_path, chunks)
    except FileNotFoundError as e:
        print(f"❌ {e}")
        sys.exit(1)
    except ValueError as e:
        print(f"❌ {e}")
        sys.exit(1)

    # Check mic availability
    mic_available = has_mic_available()
    voice_enabled = mic_available

    if not mic_available:
        print("⚠ No microphone detected. Running in text-only mode.")

    print("\n" + "=" * 60)
    print(f"Ready! Ask me about the document.")
    if voice_enabled:
        print("Commands: Press Enter to speak, or type a question, or 'exit'")
    else:
        print("Commands: Type a question or 'exit'")
    print("=" * 60 + "\n")

    relevance_threshold = float(os.getenv("RELEVANCE_THRESHOLD", "0.5"))
    tts_voice = os.getenv("TTS_VOICE", "alloy")

    while True:
        try:
            # Get question
            if voice_enabled:
                cmd = input("\n[Press Enter to speak, or type a question, or 'exit']: ").strip()

                if cmd.lower() == "exit":
                    print("Goodbye!")
                    break

                if not cmd:
                    # Empty input → record from mic
                    print("🎤 Recording...")
                    audio_bytes = record_from_mic()
                    print("📝 Transcribing...")
                    question = transcribe_audio(audio_bytes)
                    print(f"📢 You asked: {question}")
                else:
                    question = cmd
            else:
                cmd = input("\n[Type a question, or 'exit']: ").strip()

                if cmd.lower() == "exit":
                    print("Goodbye!")
                    break

                if not cmd:
                    print("Please type a question or 'exit'.")
                    continue

                question = cmd

            if not question.strip():
                print("No question detected. Try again.")
                continue

            # Query document
            print("\n🔍 Searching document...")
            answer, found, sources = query_document(
                vector_store,
                question,
                threshold=relevance_threshold
            )

            # Display answer
            print(f"\n📝 Answer:\n{answer}")

            # Speak answer
            if voice_enabled:
                speak_response(answer, voice=tts_voice)

            # Show sources
            if found and sources:
                print("\n📚 Sources:")
                for src in sources:
                    print(f"  Page {src['page']}: {src['content']}")

            # Web fallback offer
            if not found:
                web_choice = input("\nSearch the web instead? (yes/no): ").strip().lower()
                if web_choice in ["yes", "y"]:
                    print("\n🌐 Searching the web...")
                    web_answer = search_web_for_answer(question)
                    print(f"\n{web_answer}")
                    if voice_enabled:
                        speak_response(web_answer, voice=tts_voice)

        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            break
        except Exception as e:
            print(f"\n⚠ Error: {e}")
            print("Continuing... try your question again.")

if __name__ == "__main__":
    main()
