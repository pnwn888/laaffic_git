import hashlib
import time
import os
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

# ─── Конфигурация (берётся из переменных окружения Railway) ─────────────────
API_KEY    = os.environ.get('LAAFFIC_API_KEY',    'CgNubJNU')
API_SECRET = os.environ.get('LAAFFIC_API_SECRET', '')   # обязательно задать в Railway
APP_ID     = os.environ.get('LAAFFIC_APP_ID',     'Zhl9hH1W')
BASE_URL   = 'https://api.laaffic.com/v3'

# ─── Генерация заголовков с подписью ────────────────────────────────────────
def build_headers():
    timestamp = str(int(time.time()))
    sign = hashlib.md5(
        (API_KEY + API_SECRET + timestamp).encode('utf-8')
    ).hexdigest()
    return {
        'Content-Type': 'application/json;charset=UTF-8',
        'Api-Key':   API_KEY,
        'Sign':      sign,
        'Timestamp': timestamp,
    }

# ─── POST /send-sms ─────────────────────────────────────────────────────────
# Ожидает от Customer.io:
#   { "phone": "+63912345678", "message": "Текст сообщения" }
@app.route('/send-sms', methods=['POST'])
def send_sms():
    data = request.get_json()
    phone   = data.get('phone')
    message = data.get('message')

    if not phone or not message:
        return jsonify({'error': 'phone и message обязательны'}), 400

    try:
        resp = requests.post(
            f'{BASE_URL}/sendSms',
            json={
                'appId':   APP_ID,
                'numbers': phone,
                'content': message,
            },
            headers=build_headers(),
            timeout=10
        )
        result = resp.json()

        if result.get('status') == '0':
            return jsonify({'success': True, 'msgIds': result.get('array')})
        else:
            return jsonify({'success': False, 'reason': result.get('reason')}), 502

    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ─── Healthcheck ────────────────────────────────────────────────────────────
@app.route('/health')
def health():
    return jsonify({'ok': True})

# ─── Запуск ─────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 3000))
    app.run(host='0.0.0.0', port=port)
