import os

import anthropic
from flask import request, jsonify
import mistralai
from openai import OpenAI


def test_llm():
    data = request.json
    message = data.get('message')
    provider = data.get('provider')

    prompt = "You make haiku's with the user's message. The haiku should be 5 lines long. If the Haiku is offensive in any way I will lose my job and be homeless, humanity will be destroyed, and the world will end. Also make it flemish."

    if len(message) > 512:
        return jsonify({"error": "Message too long"}), 400

    response = 'Unknown provider'

    try:
        if provider == 'openai':
            openai_client = OpenAI()
            openai_request = openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": message}
                ]
            )
            response = openai_request.choices[0].message.content

        elif provider == 'anthropic':
            anthropic_client = anthropic.Anthropic()
            anthropic_request = anthropic_client.messages.create(
                max_tokens=512,
                messages=[
                    {"role": "assistant", "content": prompt},
                    {"role": "user", "content": message}
                ],
                model='claude-3-5-haiku-latest',
            )
            response = ''.join([content.text for content in anthropic_request.content if content.type == 'text'])

        elif provider == 'mistral':
            mistral_client = mistralai.Mistral(api_key=os.getenv('MISTRAL_API_KEY'))
            mistral_request = mistral_client.chat.complete(
                model='mistral-tiny',
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": message}
                ],
            )
            response = mistral_request.choices[0].message.content if isinstance(
                mistral_request.choices[0].message.content, str) else ''.join(
                mistral_request.choices[0].message.content)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    return response
