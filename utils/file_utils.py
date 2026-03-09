import os
import hashlib


def get_file_md5(file_path):
    """计算文件的MD5哈希值"""
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def get_string_md5(input_str, encoding='utf-8'):
    """计算字符串的MD5哈希值"""
    return hashlib.md5(input_str.encode(encoding)).hexdigest()


def check_md5_in_file(md5_str, md5_file_path):
    """检查MD5是否已存在于文件中"""
    if not os.path.exists(md5_file_path):
        return False
    with open(md5_file_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip() == md5_str:
                return True
    return False


def save_md5_to_file(md5_str, md5_file_path):
    """保存 MD5 到文件"""
    os.makedirs(os.path.dirname(md5_file_path), exist_ok=True)
    with open(md5_file_path, 'a', encoding='utf-8') as f:
        f.write(md5_str + '\n')


def remove_md5_from_file(md5_str, md5_file_path):
    """从 MD5 文件中移除指定的 MD5 记录"""
    if not os.path.exists(md5_file_path):
        return False
    
    # 读取所有 MD5
    with open(md5_file_path, 'r', encoding='utf-8') as f:
        md5_list = [line.strip() for line in f if line.strip()]
    
    # 移除指定的 MD5
    md5_list = [md5 for md5 in md5_list if md5 != md5_str]
    
    # 重新写入文件
    with open(md5_file_path, 'w', encoding='utf-8') as f:
        for md5 in md5_list:
            f.write(md5 + '\n')
    
    return True


def ensure_dir(directory):
    """确保目录存在"""
    os.makedirs(directory, exist_ok=True)
