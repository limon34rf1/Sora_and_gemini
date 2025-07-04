from flask import Flask, request, jsonify
import os
import re
import requests
from google import genai

GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', 'AIzaSyBjCMFPAv1QX5ewcb0m08Pjh4Mdn6MV9i8')
SORA_API_KEY = os.getenv('SORA_API_KEY', 'sk-bCREbtCgwOgFPHxdFd4c7a9910A140438507D1C51401827c')
SORA_URL = "https://api.laozhang.ai/v1/chat/completions"

genai_client = genai.Client(api_key=GEMINI_API_KEY)
app = Flask(__name__)

@app.route('/', methods=['GET'])
def generate():
    query_text = request.args.get('query', '')
    if not query_text:
        return jsonify({'error': 'Missing query parameter'}), 400

    try:
        prompt_request = (
            "Напиши очень подробный промпт для Sora, кроме промпта не должно быть лишних слов. "
            "Задача — нарисовать картинку в лучшем виде, не придумывать ничего лишнего, "
            "главная задача — сохранить исходную идею. Ниже запрос пользователя, ответ дай на английском языке:\n"
            f"{query_text}"
        )
        response = genai_client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt_request
        )
        best_prompt = response.text.strip()
    except Exception as e:
        return jsonify({'error': f'Gemini error: {str(e)}'}), 500

    headers = {
        "Authorization": f"Bearer {SORA_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": "sora-image",
        "stream": False,
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user",   "content": best_prompt}
        ],
    }
    try:
        resp = requests.post(SORA_URL, headers=headers, json=payload)
        resp.raise_for_status()
        data = resp.json()
        content = data["choices"][0]["message"]["content"]
        image_urls = re.findall(r"\((https?://[^\s)]+)\)", content)
        if image_urls:
            return jsonify({'image_url': image_urls[0]})
        return jsonify({'error': 'No image URL found in Sora response'}), 500
    except Exception as e:
        return jsonify({'error': f'Sora API error: {str(e)}'}), 500
