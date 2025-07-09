import re
from openai import OpenAI

def analyze_voice_content(
    wav_path,
    openai_api_key,
    whisper_model="whisper-1",
    gpt_model="gpt-4.1-mini",
):
    """
    - Transcribes wav_path using Whisper.
    - Runs GPT-4-mini phishing analysis.
    - Returns (transcript_text, phishing_scores_dict)
    """
    client = OpenAI(api_key=openai_api_key)

    # Step 1: Transcribe
    with open(wav_path, "rb") as audio_file:
        transcription = client.audio.transcriptions.create(
            model=whisper_model,
            file=audio_file
        )
    transcript_text = transcription.text

    # Step 2: Analyze content with GPT-4-mini
    response = client.chat.completions.create(
        model=gpt_model,
        messages=[
            {"role": "system", "content": "You are a security system that detects phishing content."},
            {"role": "user", "content": f"""
Analyze the following text for signs of phishing. For each of the following categories, assign a score from 0 to 10 based on severity or likelihood:

1. Asking for money
2. Asking for password
3. Asking for personal information
4. Other suspicious content

ONLY respond with the scores in this format:

asking_for_money: <score>
asking_for_password: <score>
asking_for_personal_info: <score>
other_suspicious_content: <score>

Text:
\"\"\"{transcript_text}\"\"\"
"""}
        ],
        temperature=0.2,
        max_tokens=150,
        top_p=1.0
    )
    gpt_out = response.choices[0].message.content

    # Parse out phishing category scores as integers
    voice_scores = {
        "asking_for_money": 0,
        "asking_for_password": 0,
        "asking_for_personal_info": 0,
        "other_suspicious_content": 0,
    }
    for k in voice_scores:
        m = re.search(rf"{k}:\s*(\d+)", gpt_out)
        if m:
            voice_scores[k] = int(m.group(1))

    # return transcript_text, voice_scores
    return {
    'transcript': transcript_text,
    'voice_content_scores': voice_scores,
    'gpt_response': gpt_out,
}


