import re
import json
import argparse
import os

def try_read_file(file_path):
    """尝试多种编码读取文件，解决中文编码问题"""
    encodings = ['utf-8', 'gbk', 'gb2312', 'gb18030', 'latin-1']
    
    for encoding in encodings:
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                content = f.read()
            print(f"✅ 成功使用 [{encoding}] 编码读取文件")
            return content
        except UnicodeDecodeError:
            continue
    
    print("\n" + "="*60)
    print("❌ 错误：无法读取文件")
    print("="*60)
    print("📌 解决方案：")
    print("   1. 用记事本打开「专8.txt」")
    print("   2. 点击「文件」→「另存为」")
    print("   3. 编码选择「UTF-8」")
    print("   4. 保存后重新运行脚本")
    print("="*60)
    return None

def clean_text(text):
    """
    专八文档专用清洗函数
    1. 去除所有不可见控制字符
    2. 去除开头的空白和乱码
    3. 规范中间的空白字符
    """
    # 1. 去除所有ASCII控制字符（0x00-0x1F和0x7F），这是乱码的主要来源
    text = re.sub(r'[\x00-\x1F\x7F]', '', text)
    
    # 2. 去除开头的所有非有效字符（直到遇到字母或中文）
    # 有效起始字符定义：英文(a-z/A-Z)、中文(\u4e00-\u9fff)、数字(0-9)
    text = re.sub(r'^[^a-zA-Z\u4e00-\u9fff0-9]+', '', text)
    
    # 3. 将中间连续的多个空白字符替换为单个空格
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text

def parse_tem8_vocab(file_path):
    """
    解析专八词汇表（乱码修复版）
    """
    vocab_list = []
    
    # 尝试读取文件
    content = try_read_file(file_path)
    if content is None:
        return []
    
    # 按行分割文本
    lines = content.split('\n')
    print(f"✅ 成功加载文档，共 {len(lines)} 行数据")

    # 列表标题行正则
    list_title_pattern = re.compile(r'^[Ll]ist\s+\d+')

    for line_idx, line in enumerate(lines):
        line = line.strip()
        
        # 跳过空行和标题行
        if not line or list_title_pattern.match(line):
            continue
        
        # 策略：先按空白分割，取第一个非空字符为单词
        # 剩余部分全部交给 clean_text 函数清洗
        parts = line.split()
        
        if len(parts) >= 2:
            word = parts[0]
            # 剩余部分重新拼接后清洗
            raw_trans = ' '.join(parts[1:])
            clean_trans = clean_text(raw_trans)
            
            if clean_trans: # 确保清洗后不为空
                vocab_list.append({
                    "english": word,
                    "chinese_trans": clean_trans,
                    "spell": None
                })
            else:
                print(f"⚠️  清洗后为空行 {line_idx+1}：{line}")
        else:
            print(f"⚠️  跳过异常行 {line_idx+1}：{line}")

    print(f"✅ 解析完成，共提取 {len(vocab_list)} 个有效词汇")
    return vocab_list

def save_to_json(vocab_list, output_path):
    """按标准格式保存为JSON文件"""
    if not vocab_list:
        print("❌ 没有有效词汇，跳过JSON保存")
        return
        
    json_data = {}
    for idx, vocab in enumerate(vocab_list, start=1):
        json_data[str(idx)] = vocab

    os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else ".", exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(json_data, f, ensure_ascii=False, indent=4)

    abs_path = os.path.abspath(output_path)
    file_size_kb = os.path.getsize(output_path) / 1024
    print(f"📁 JSON文件已保存：{abs_path}")
    print(f"💾 文件大小：约 {file_size_kb:.1f} KB")
    return json_data

def main():
    parser = argparse.ArgumentParser(description="专八英语大纲词汇 纯文本→JSON 转换工具 (乱码修复版)")
    parser.add_argument("-i", "--input", required=True, help="输入文件路径（请使用 .txt 纯文本）")
    parser.add_argument("-o", "--output", default="resource/TEM8_Vocabulary.json", help="输出JSON文件路径")
    args = parser.parse_args()

    if not os.path.exists(args.input):
        print(f"❌ 错误：输入文件不存在 - {args.input}")
        return

    print("=" * 60)
    print("🎯 专八英语大纲词汇表 转换工具 (乱码修复版)")
    print("📌 核心修复：自动去除不可见控制字符乱码")
    print("=" * 60)

    vocab_list = parse_tem8_vocab(args.input)
    save_to_json(vocab_list, args.output)

    if vocab_list:
        print("=" * 60)
        print("🎉 转换完成！乱码已清除")
        print("=" * 60)

if __name__ == "__main__":
    main()