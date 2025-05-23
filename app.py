from flask import Flask, render_template, request, send_from_directory, redirect
import os
import random
import string

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['SECRET_KEYS'] = {}

def generate_key(length):
    # 修改字符集包含数字+大写字母+小写字母
    chars = string.digits + string.ascii_letters
    return ''.join(random.choices(chars, k=length))


@app.route('/')
def index():
    """
    首页路由处理函数
    返回渲染后的index.html模板页面
    """
    return render_template('home.html')  # 修改为新的首页模板


@app.route('/upload')
def upload_page():
    """文件上传页面路由"""
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    """
    处理文件上传的API端点。
    接收POST请求，保存上传的文件到服务器，并生成唯一密钥用于后续访问。
    
    路由:
        POST /upload
    
    参数:
        files: 上传的文件列表
        key_length: 生成密钥的长度
    
    返回:
        重定向到上传成功页面，附带生成的密钥
    """
    files = request.files.getlist('files')
    key_length = int(request.form['key_length'])
    secret_key = generate_key(key_length)
    
    # 保存文件
    save_path = os.path.join(app.config['UPLOAD_FOLDER'], secret_key)
    os.makedirs(save_path, exist_ok=True)
    
    filenames = []
    for file in files:
        file.save(os.path.join(save_path, file.filename))
        filenames.append(file.filename)
    
    app.config['SECRET_KEYS'][secret_key] = filenames
    # 修改为重定向到新路由防止重复提交
    return redirect(f'/upload/success/{secret_key}')

# 新增GET路由显示上传结果
@app.route('/upload/success/<secret_key>')
def upload_success(secret_key):
    if secret_key not in app.config['SECRET_KEYS']:
        return redirect('/')
    return render_template('upload_success.html', secret_key=secret_key)

@app.route('/download', methods=['GET', 'POST'])
def download():
    if request.method == 'POST':
        secret_key = request.form['secret_key']
        if secret_key in app.config['SECRET_KEYS']:
            return redirect(f'/download/{secret_key}')
        return '无效的密钥'
    return render_template('download.html')

@app.route('/download/<key>')
def download_files(key):
    if key not in app.config['SECRET_KEYS']:
        return '密钥无效'
    return render_template('download.html', files=app.config['SECRET_KEYS'][key], key=key)

@app.route('/download/<key>/<filename>')
def download_file(key, filename):
    directory = os.path.join(app.config['UPLOAD_FOLDER'], key)
    return send_from_directory(directory, filename, as_attachment=True)

if __name__ == '__main__':
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    app.run(debug=True)