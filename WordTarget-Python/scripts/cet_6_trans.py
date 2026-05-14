import re
import json
import argparse
import os

def try_read_file(file_path):
    """尝试多种编码读取文件，解决中文编码问题"""
    encodings = ['utf-8', 'gbk', 'gb2312', 'gb18030', 'latin-1']
    # encodings = ['gbk']
    for encoding in encodings:
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                content = f.read()
            print(f"✅ 成功使用 [{encoding}] 编码读取文件")
            return content
        except UnicodeDecodeError:
            continue
    
    # 所有编码都失败
    print("\n" + "="*60)
    print("❌ 错误：无法直接读取 .doc 二进制文件")
    print("="*60)
    print("📌 解决方案：")
    print("   1. 用 Microsoft Word 打开「六级大纲词汇.doc」")
    print("   2. 点击「文件」→「另存为」")
    print("   3. 选择文件类型为「纯文本 (*.txt)」")
    print("   4. 编码选择「UTF-8」")
    print("   5. 保存后，使用该 .txt 文件作为输入")
    print("="*60)
    return None

def parse_cet6_vocab(file_path):
    """
    解析纯文本格式六级词汇表
    每行格式：若干空格 + 单词 + 若干空格 + 词性+中文翻译
    音标固定为 null
    """
    vocab_list = []
    
    # 尝试读取文件
    content = try_read_file(file_path)
    if content is None:
        return []
    
    # 按行分割文本
    lines = content.split('\n')
    print(f"✅ 成功加载文档，共 {len(lines)} 行数据")

    for line_idx, line in enumerate(lines):
        # 去除首尾所有空白字符
        line = line.strip()
        
        # 跳过无效行：空行、Markdown表头、分隔线、末尾的|
        if (not line 
            or line.startswith('|六级大纲单词|') 
            or line.startswith('|---|') 
            or line == '|'):
            continue
        
        # 核心分割逻辑：以2个及以上连续空格为分隔符，最多分割1次
        # 完美区分"单词"和"包含空格的翻译部分"
        parts = re.split(r'\s{2,}', line, maxsplit=1)
        
        if len(parts) == 2:
            word, chinese = parts
            # 二次清理首尾可能残留的空格
            word = word.strip()
            chinese = chinese.strip()
            
            vocab_list.append({
                "english": word,
                "chinese_trans": chinese,
                "spell": None  # 无音标，统一设为null
            })
        else:
            # 打印异常行便于排查（可选，太多可注释）
            # print(f"⚠️  跳过异常行 {line_idx+1}：{line}")
            pass

    print(f"✅ 解析完成，共提取 {len(vocab_list)} 个有效词汇")
    return vocab_list

def save_to_json(vocab_list, output_path):
    """按标准格式保存为JSON文件"""
    if not vocab_list:
        print("❌ 没有有效词汇，跳过JSON保存")
        return
        
    json_data = {}
    # 从1开始编号，与之前中考词汇格式完全一致
    for idx, vocab in enumerate(vocab_list, start=1):
        json_data[str(idx)] = vocab

    # 自动创建输出目录
    os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else ".", exist_ok=True)

    # 写入文件：中文不转义、格式化缩进
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(json_data, f, ensure_ascii=False, indent=4)

    # 输出文件信息
    abs_path = os.path.abspath(output_path)
    file_size_kb = os.path.getsize(output_path) / 1024
    print(f"📁 JSON文件已保存：{abs_path}")
    print(f"💾 文件大小：约 {file_size_kb:.1f} KB")
    return json_data

def main():
    parser = argparse.ArgumentParser(description="六级英语大纲词汇 纯文本→JSON 转换工具")
    parser.add_argument("-i", "--input", required=True, help="输入文件路径（请使用 .txt 纯文本）")
    parser.add_argument("-o", "--output", default="resource/CET6_Vocabulary.json", help="输出JSON文件路径")
    args = parser.parse_args()

    # 检查输入文件是否存在
    if not os.path.exists(args.input):
        print(f"❌ 错误：输入文件不存在 - {args.input}")
        return

    # 打印工具信息
    print("=" * 60)
    print("🎯 六级英语大纲词汇表 转换工具")
    print("📌 输入格式：纯文本 .txt (请勿直接使用 .doc)")
    print("📌 输出格式：与中考词汇完全兼容的JSON")
    print("📌 音标字段：自动填充为 null")
    print("=" * 60)

    # 执行转换
    vocab_list = parse_cet6_vocab(args.input)
    save_to_json(vocab_list, args.output)

    # 完成提示
    if vocab_list:
        print("=" * 60)
        print("🎉 转换完成！可直接用于单词射击游戏词库")
        print("=" * 60)

if __name__ == "__main__":
    main()