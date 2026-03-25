import hashlib
import time
import os
import logging
import requests
from flask import Flask, request, jsonify

logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)
app.logger.setLevel(logging.DEBUG)

# ─── Конфигурация (берётся из переменных окружения Railway) ─────────────────
API_KEY    = os.environ.get('LAAFFIC_API_KEY',    '')
API_SECRET = os.environ.get('LAAFFIC_API_SECRET', '')
APP_ID     = os.environ.get('LAAFFIC_APP_ID',     '')
BASE_URL   = 'https://api.laaffic.com/v3'

# ─── Генерация заголовков с подписью ────────────────────────────────────────
def build_headers():
    timestamp = str(int(time.time()))
    sign = hashlib.md5(
        (API_KEY + API_SECRET + timestamp).encode('utf-8')
    ).hexdigest()
    app.logger.debug(f"API_KEY={API_KEY}, APP_ID={APP_ID}, timestamp={timestamp}, sign={sign}")
    return {
        'Content-Type': 'application/json;charset=UTF-8',
        'Api-Key':   API_KEY,
        'Sign':      sign,
        'Timestamp': timestamp,
    }

# ─── POST /send-sms ─────────────────────────────────────────────────────────
@app.route('/send-sms', methods=['POST'])
def send_sms():
    data = request.get_json()
    phone   = data.get('phone')
    message = data.get('message')

    app.logger.debug(f"Received request: phone={phone}, message={message}")

    if not phone or not message:
        return jsonify({'error': 'phone и message обязательны'}), 400

    try:
        headers = build_headers()
        payload = {
            'appId':   APP_ID,
            'numbers': phone,
            'content': message,
        }
        app.logger.debug(f"Sending to Laaffic: {payload}")

        resp = requests.post(
            f'{BASE_URL}/sendSms',
            json=payload,
            headers=headers,
            timeout=10
        )
        app.logger.debug(f"Laaffic response: status={resp.status_code}, body={resp.text}")

        result = resp.json()

        if result.get('status') == '0':
            return jsonify({'success': True, 'msgIds': result.get('array')})
        else:
            return jsonify({'success': False, 'reason': result.get('reason'), 'raw': result}), 502

    except Exception as e:
        app.logger.error(f"Exception: {e}")
        return jsonify({'error': str(e)}), 500

# ─── Healthcheck ────────────────────────────────────────────────────────────
@app.route('/health')
def health():
    return jsonify({'ok': True, 'api_key_set': bool(API_KEY), 'secret_set': bool(API_SECRET), 'app_id_set': bool(APP_ID)})

# ─── Запуск ─────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 3000))
    app.run(host='0.0.0.0', port=port)
