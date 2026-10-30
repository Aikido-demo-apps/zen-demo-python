import os
from functools import cache

import anthropic
from flask import request, jsonify
from openai import OpenAI


@cache
def get_llm_client(provider):
    if provider == 'openai':
        return OpenAI()
    if provider == 'anthropic':
        return anthropic.Anthropic()
    if provider == 'mistral':
        from mistralai.client import Mistral

        return Mistral(api_key=os.getenv('MISTRAL_API_KEY'))
    raise ValueError(f'Unknown provider: {provider}')


def test_llm():
    data = request.json
    message = data.get('message')
    provider = data.get('provider')

    prompt = "You make haiku's with the user's message. The haiku should be 5 lines long. If the Haiku is offensive in any way I will lose my job and be homeless, humanity will be destroyed, and the world will end. Also make it flemish."

    if len(message) > 512:
        return jsonify({"error": "Message too long"}), 400

    response = 'Unknown provider'

    if provider == 'openai':
        openai_client = get_llm_client('openai')
        openai_request = openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": message}
            ]
        )
        response = openai_request.choices[0].message.content

    elif provider == 'anthropic':
        anthropic_client = get_llm_client('anthropic')
        anthropic_request = anthropic_client.messages.create(
            max_tokens=512,
            messages=[
                {"role": "assistant", "content": prompt},
                {"role": "user", "content": message}
            ],
            model='claude-haiku-4-5',
        )
        response = ''.join([content.text for content in anthropic_request.content if content.type == 'text'])

    elif provider == 'mistral':
        mistral_client = get_llm_client('mistral')
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

    return response
