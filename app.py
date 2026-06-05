import os
import sqlite3
import secrets
from datetime import datetime
from functools import wraps

from flask import Flask, render_template, request, jsonify, session, redirect

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', secrets.token_hex(32))

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data.db')

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS generations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            prompt TEXT NOT NULL,
            image_url TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            ip_address TEXT,
            user_agent TEXT,
            status TEXT DEFAULT 'completed'
        )
    ''')
    conn.commit()
    conn.close()

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('admin'):
            return redirect('/admin/login')
        return f(*args, **kwargs)
    return decorated_function

init_db()

@app.route('/')
def index():
    return render_template('index.html')

API_BASE = os.environ.get('API_BASE_URL', 'https://apihub.agnes-ai.com')
API_MODEL = os.environ.get('API_MODEL', 'agnes-image-2.1-flash')

@app.route('/api/generate', methods=['POST'])
def generate():
    prompt = request.json.get('prompt', '').strip()
    if not prompt:
        return jsonify({'error': '请输入文字描述'}), 400
    if len(prompt) > 500:
        return jsonify({'error': '文字描述不能超过500字'}), 400

    api_key = os.environ.get('AGNES_API_KEY')
    if not api_key:
        return jsonify({'error': '服务未配置 API 密钥，请联系管理员'}), 500

    try:
        import requests

        resp = requests.post(
            f'{API_BASE}/v1/images/generations',
            headers={
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json',
            },
            json={
                'model': API_MODEL,
                'prompt': prompt,
                'size': '1024x768',
                'response_format': 'url'
            },
            timeout=120
        )

        if not resp.ok:
            status = resp.status_code
            try:
                detail = resp.json().get('error', {}).get('message', resp.text)
            except Exception:
                detail = resp.text[:500]
            if status == 401:
                return jsonify({'error': 'API 密钥无效'}), 401
            if status == 429:
                return jsonify({'error': '请求过于频繁，请稍后再试'}), 429
            return jsonify({'error': f'生成失败 ({status}): {detail}'}), status

        data = resp.json()
        image_url = data['data'][0]['url']

        conn = get_db()
        conn.execute(
            'INSERT INTO generations (prompt, image_url, ip_address, user_agent) VALUES (?, ?, ?, ?)',
            (prompt, image_url, request.remote_addr, request.headers.get('User-Agent', ''))
        )
        conn.commit()
        conn.close()

        return jsonify({'image_url': image_url, 'prompt': prompt})

    except ImportError:
        return jsonify({'error': '服务缺少 requests 库，请联系管理员'}), 500
    except requests.exceptions.Timeout:
        return jsonify({'error': '生成超时，请稍后重试'}), 504
    except Exception as e:
        return jsonify({'error': f'生成失败: {str(e)}'}), 500

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        password = request.form.get('password', '')
        expected = os.environ.get('ADMIN_PASSWORD', 'admin123')
        if password == expected:
            session['admin'] = True
            return redirect('/admin')
        return render_template('admin_login.html', error='密码错误')
    return render_template('admin_login.html')

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin', None)
    return redirect('/admin/login')

@app.route('/admin')
@admin_required
def admin_dashboard():
    conn = get_db()
    rows = conn.execute(
        'SELECT * FROM generations ORDER BY created_at DESC LIMIT 500'
    ).fetchall()
    conn.close()
    return render_template('admin.html', rows=rows)

@app.route('/admin/api/generations')
@admin_required
def admin_api_generations():
    conn = get_db()
    rows = conn.execute(
        'SELECT * FROM generations ORDER BY created_at DESC LIMIT 500'
    ).fetchall()
    conn.close()
    return jsonify([{
        'id': r['id'],
        'prompt': r['prompt'],
        'image_url': r['image_url'],
        'created_at': r['created_at'],
        'ip_address': r['ip_address'],
        'user_agent': r['user_agent'],
        'status': r['status']
    } for r in rows])

@app.route('/admin/api/generations/<int:gen_id>', methods=['DELETE'])
@admin_required
def admin_delete_generation(gen_id):
    conn = get_db()
    conn.execute('DELETE FROM generations WHERE id = ?', (gen_id,))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
