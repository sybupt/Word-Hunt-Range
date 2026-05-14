import pandas as pd
import json
import argparse
import os

def clean_text(text):
    """清理文本：去除空格、空值处理"""
    if pd.isna(text) or text is None:
        return None
    text = str(text).strip()
    return text if text else None

def is_group_letter(text):
    """判断是否为词汇分组大写字母（A-Z）"""
    text = clean_text(text)
    return text is not None and len(text) == 1 and text.isalpha() and text.isupper()

def parse_gaokao_vocab_excel(excel_path):
    """
    解析高考英语核心词汇Excel（适配真实8列/4列结构）
    返回：词汇列表 [{"english": "", "spell": "", "chinese_trans": ""}]
    """
    # 读取Excel（不使用表头，读取所有行）
    df = pd.read_excel(excel_path, header=None, engine="xlrd")
    vocab_list = []
    
    print(f"✅ 读取表格完成，共 {len(df)} 行数据")
    
    # 遍历每一行
    for row_idx in range(len(df)):
        row = df.iloc[row_idx]
        # 获取当前行所有非空单元格
        cells = [clean_text(cell) for cell in row if clean_text(cell) is not None]
        
        # 1. 空行 → 跳过
        if len(cells) == 0:
            continue
            
        # 2. 分组大写字母行（A/B/C…）或标题行 → 跳过
        if len(cells) == 1:
            continue
            
        # 3. 按每4个元素分块解析（支持4列单单词或8列双单词）
        # 结构：[单词, 音标, 词性, 中文]
        for i in range(0, len(cells), 4):
            chunk = cells[i:i+4]
            # 确保块长度为4（单词+音标+词性+中文）
            if len(chunk) < 4:
                print(f"⚠️  跳过行 {row_idx+1} 的不完整块：{chunk}")
                continue
            
            word, spell, pos, chinese = chunk
            vocab_list.append({
                "english": word,
                "spell": spell,
                "chinese_trans": chinese  # 仅取中文释义，忽略词性
            })
    
    print(f"✅ 解析完成，共提取 {len(vocab_list)} 个有效单词")
    return vocab_list

def save_to_target_json(vocab_list, output_path):
    """按要求格式保存为JSON：{索引: {"english":"", "chinese_trans":"", "spell":""}}"""
    json_data = {}
    # 索引从1开始连续编号
    for idx, vocab in enumerate(vocab_list, start=1):
        json_data[str(idx)] = {
            "english": vocab["english"],
            "chinese_trans": vocab["chinese_trans"],
            "spell": vocab["spell"]
        }
    
    # 确保输出目录存在
    os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else ".", exist_ok=True)
    
    # 写入JSON（中文正常显示，缩进4格）
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(json_data, f, ensure_ascii=False, indent=4)
    
    print(f"📁 成功导出JSON：{os.path.abspath(output_path)}")
    return json_data

def main():
    parser = argparse.ArgumentParser(description="高考英语核心词汇 Excel → JSON（修复版）")
    parser.add_argument("-i", "--input", required=True, help="输入Excel文件路径")
    parser.add_argument("-o", "--output", default="gaokao_vocab.json", help="输出JSON路径（默认gaokao_vocab.json）")
    args = parser.parse_args()
    
    if not os.path.exists(args.input):
        print(f"❌ 输入文件不存在：{args.input}")
        return
    
    # 执行解析+导出
    print("=" * 50)
    print("🎯 高考英语核心词汇 Excel → JSON（修复版）")
    print("=" * 50)
    
    vocab_list = parse_gaokao_vocab_excel(args.input)
    save_to_target_json(vocab_list, args.output)
    
    print("=" * 50)
    print("🎉 全部完成！")
    print("=" * 50)

if __name__ == "__main__":
    # 检查依赖
    try:
        import pandas
        import xlrd
    except ImportError:
        print("⚠️  缺少依赖，请执行：pip install pandas xlrd")
        exit(1)
    
    main()