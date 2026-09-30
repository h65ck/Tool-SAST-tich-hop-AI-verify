import json
import logging
import os
from google import genai
from google.genai import types

logger = logging.getLogger(__name__)

# TODO: Thay thế bằng API Key thật của bạn
GEMINI_API_KEY = "AQ.Ab8RN6LtAXmKMehqEOtwScle0eksM-8sKdovDjXeE_Kl5NZi8Q"

def review(prompt: str) -> dict:
    if GEMINI_API_KEY == "YOUR_API_KEY_HERE":
        return {
            "status": "need_more_context",
            "confidence": 0,
            "severity": "Info",
            "reason": "AI Verification failed: API Key is not configured.",
            "recommendation": "Vui lòng cung cấp Gemini API Key trong file config.py."
        }

    try:
        import time
        client = genai.Client(api_key=GEMINI_API_KEY)
        
        response = None
        last_error = None
        for attempt in range(3):
            try:
                response = client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        temperature=0.2,
                    ),
                )
                break
            except Exception as e:
                last_error = e
                if attempt < 2 and "503" in str(e):
                    time.sleep(2)  # Wait 2 seconds before retrying
                else:
                    raise e
                    
        content = response.text.strip()
        
        # Clean up potential markdown blocks
        if content.startswith("```json"):
            content = content[7:]
        if content.endswith("```"):
            content = content[:-3]
            
        return json.loads(content.strip())
        
    except Exception as e:
        logger.error(f"Error calling Gemini API: {e}")
        return {
            "status": "need_more_context",
            "confidence": 0,
            "severity": "Info",
            "reason": f"AI Verification failed due to exception: {str(e)}",
            "recommendation": "Check API connection and API Key."
        }
