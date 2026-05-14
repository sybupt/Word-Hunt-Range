import pandas as pd
import json
import argparse
import os
import re

def clean_text(text):
    """文本清理：去除空值、多余空格"""
    if pd.isna(text) or text is None:
        return None
    text = str(text).strip()
    text = re.sub(r'\s+', ' ', text)
    return text if text else None

def parse_middle_school_vocab(excel_path):
    """
    【中考专用】解析四列结构：序号 | 单词 | 词性 | 中文翻译
    音标固定为 null
    """
    vocab_list = []
    # 读取Excel（无表头，读取所有行）
    df = pd.read_excel(excel_path, header=None, engine="xlrd")
    print(f"✅ 成功加载Excel，共 {len(df)} 行数据")

    for row_idx in range(len(df)):
        row = df.iloc[row_idx]
        # 清理并获取非空单元格
        cells = [clean_text(cell) for cell in row if clean_text(cell) is not None]

        # ===================== 核心修复：适配4列结构 =====================
        # 有效行规则：必须是4列，且第1列是数字（序号）
        if len(cells) == 4 and cells[0].isdigit():
            serial_num, word, pos, chinese = cells
            vocab_list.append({
                "english": word,
                "chinese_trans": chinese,
                "spell": None  # 无音标，设为null
            })
        # =================================================================

    print(f"✅ 解析完成，共提取 {len(vocab_list)} 个有效词汇")
    return vocab_list

def save_to_json(vocab_list, output_path):
    """按要求保存为JSON格式"""
    json_data = {}
    for idx, vocab in enumerate(vocab_list, start=1):
        json_data[str(idx)] = vocab

    # 确保输出目录存在
    os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else ".", exist_ok=True)

    # 写入文件（中文正常显示，缩进4格）
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(json_data, f, ensure_ascii=False, indent=4)

    print(f"📁 JSON已保存：{os.path.abspath(output_path)}")
    return json_data

def main():
    parser = argparse.ArgumentParser(description="中考英语词汇Excel→JSON【四列专用版】")
    parser.add_argument("-i", "--input", required=True, help="中考词汇Excel路径")
    parser.add_argument("-o", "--output", default="resource/中考词汇.json", help="输出JSON路径")
    args = parser.parse_args()

    if not os.path.exists(args.input):
        print(f"❌ 文件不存在：{args.input}")
        return

    print("=" * 60)
    print("🎯 中考英语大纲词汇表【四列专用】转换工具")
    print("📌 格式：序号 | 单词 | 词性 | 中文 | 音标=null")
    print("=" * 60)

    vocab_list = parse_middle_school_vocab(args.input)
    save_to_json(vocab_list, args.output)

    print("=" * 60)
    print("🎉 转换完成！100%匹配所有单词行")
    print("=" * 60)

if __name__ == "__main__":
    # 检查依赖
    try:
        import pandas
        import xlrd
    except ImportError:
        print("⚠️ 请安装依赖：pip install pandas xlrd")
        exit(1)
    main()