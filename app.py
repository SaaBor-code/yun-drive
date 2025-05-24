from flask import Flask, render_template, request, send_from_directory, redirect
import os
import random
import string
import json
import zipfile  # 新增zipfile模块导入
import shutil  # 新增shutil模块用于删除目录

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['SECRET_KEYS'] = {}

# 新增持久化功能
SECRET_KEYS_FILE = 'secret_keys.json'

def load_secret_keys():
    """从文件加载密钥数据"""
    try:
        if os.path.exists(SECRET_KEYS_FILE):
            with open(SECRET_KEYS_FILE, 'r') as f:
                app.config['SECRET_KEYS'] = json.load(f)
    except Exception as e:
        with open(SECRET_KEYS_FILE, 'w') as f:
            f.write("{}")
        print(f"加载密钥数据失败: {e}")

def save_secret_keys():
    """保存密钥数据到文件"""
    try:
        with open(SECRET_KEYS_FILE, 'w') as f:
            json.dump(app.config['SECRET_KEYS'], f)
    except Exception as e:
        print(f"保存密钥数据失败: {e}")

def generate_key(length):
    # 修改字符集包含数字+大写字母+小写字母
    chars = string.digits + string.ascii_letters
    return ''.join(random.choices(chars, k=length))


@app.route('/')
def index():
    return render_template('home.html', 
                          total_keys=len(app.config['SECRET_KEYS']))  # 确保这里计算的是字典键的数量


@app.route('/upload')
def upload_page():
    """文件上传页面路由"""
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    files = request.files.getlist('files')
    key_length = int(request.form['key_length'])
    secret_key = generate_key(key_length)
    
    # 保存文件
    save_path = os.path.join(app.config['UPLOAD_FOLDER'], secret_key)
    os.makedirs(save_path, exist_ok=True)
    
    filenames = []
    for file in files:
        file_path = os.path.join(save_path, file.filename)
        file.save(file_path)
        filenames.append(file.filename)
    
    # 修改ZIP存储路径到zip_files目录
    zip_dir = os.path.join(app.config['UPLOAD_FOLDER'], 'zip_files')
    os.makedirs(zip_dir, exist_ok=True)
    zip_path = os.path.join(zip_dir, f'{secret_key}.zip')
    with zipfile.ZipFile(zip_path, 'w') as zipf:
        for filename in filenames:
            file_path = os.path.join(save_path, filename)
            zipf.write(file_path, arcname=filename)

    # 新增文件大小检查逻辑
    zip_size = os.path.getsize(zip_path)
    max_size = 30 * 1024 * 1024  # 30MB限制
    if zip_size > max_size:
        # 清理已创建的文件和目录
        os.remove(zip_path)
        shutil.rmtree(save_path)
        return render_template('error.html', 
                             message='文件总大小超过30MB，无法上传！',
                             subtitle='上传限制提示')

    app.config['SECRET_KEYS'][secret_key] = filenames
    save_secret_keys()
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

# 修改ZIP下载路由路径
@app.route('/download/<key>/zip')
def download_zip(key):
    if key not in app.config['SECRET_KEYS']:
        return '密钥无效'
    zip_dir = os.path.join(app.config['UPLOAD_FOLDER'], 'zip_files')  # 修改下载路径
    return send_from_directory(zip_dir, f'{key}.zip', as_attachment=True, mimetype='application/zip')  # 修改文件名匹配

if __name__ == '__main__':
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    # 创建zip存储目录
    os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'zip'), exist_ok=True)
    load_secret_keys()  # 新增加载已有密钥
    app.run(debug=True)