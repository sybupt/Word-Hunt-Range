"""
大学英语四级词汇表Excel转JSON工具
功能：将Excel格式的四级词汇表转换为指定结构的JSON文件
输出格式：
{
    "index": {
        "english": "word",
        "chinese_trans": "中文翻译",
        "spell": "音标"
    }
}
其中index为数字索引，缺失值将置为null
"""

import pandas as pd
import json
import os
import argparse

def convert_cet4_vocab_to_json(excel_path, output_json_path):
    """
    将大学英语四级词汇Excel文件转换为指定格式的JSON文件
    
    参数:
    excel_path: Excel文件路径
    output_json_path: 输出JSON文件路径
    
    返回:
    bool: 转换成功返回True，失败返回False
    """
    try:
        # 读取Excel文件
        print(f"[INFO] 正在读取Excel文件: {excel_path}")
        # 尝试读取Excel文件，处理不同编码情况
        try:
            df = pd.read_excel(excel_path, sheet_name=0)
        except UnicodeDecodeError:
            try:
                df = pd.read_excel(excel_path, sheet_name=0, encoding='gbk')
            except:
                df = pd.read_excel(excel_path, sheet_name=0, encoding='utf-8')
        
        # 验证必要的列是否存在
        required_columns = ['序号', '单词', '音标', '释义']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            print(f"[ERROR] Excel文件缺少必要的列: {', '.join(missing_columns)}")
            print(f"[ERROR] 请确保Excel文件包含以下列: {', '.join(required_columns)}")
            return False
        
        # 查看数据基本信息
        print(f"[INFO] 数据总行数: {len(df)}")
        print(f"[INFO] 列名: {list(df.columns)}")
        
        # 检查数据质量
        print(f"[INFO] 数据缺失情况:")
        missing_info = df.isnull().sum()
        for col, count in missing_info.items():
            if count > 0:
                print(f"[INFO]   {col}: {count} 个缺失值")
            else:
                print(f"[INFO]   {col}: 无缺失值")
        
        # 准备JSON数据
        json_data = {}
        processed_count = 0
        
        # 遍历每一行数据
        for index, row in df.iterrows():
            try:
                # 使用Excel中的序号作为JSON的索引（确保为字符串类型）
                json_index = str(int(row['序号']))
                
                # 构建每个单词的信息字典，处理缺失值
                word_info = {
                    "english": row['单词'] if pd.notna(row['单词']) else None,
                    "chinese_trans": row['释义'] if pd.notna(row['释义']) else None,
                    "spell": row['音标'] if pd.notna(row['音标']) else None
                }
                
                # 添加到JSON数据中
                json_data[json_index] = word_info
                processed_count += 1
                
            except Exception as row_e:
                print(f"[WARNING] 处理第{index+1}行数据时出错: {str(row_e)}，已跳过该行")
                continue
        
        # 保存为JSON文件，使用缩进4格，确保中文正常显示
        print(f"[INFO] 正在生成JSON文件: {output_json_path}")
        with open(output_json_path, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, ensure_ascii=False, indent=4)
        
        print(f"[SUCCESS] 转换完成！")
        print(f"[SUCCESS] 总共处理: {len(df)} 行数据")
        print(f"[SUCCESS] 成功转换: {processed_count} 个单词")
        print(f"[SUCCESS] JSON文件已保存至: {output_json_path}")
        
        # 显示前3个条目的示例
        print("\n[INFO] JSON格式示例（前3个单词）:")
        sample_count = min(3, processed_count)
        sample_data = {k: json_data[k] for k in list(json_data.keys())[:sample_count]}
        print(json.dumps(sample_data, ensure_ascii=False, indent=4))
        
        return True
        
    except Exception as e:
        print(f"[ERROR] 转换过程中出现严重错误: {str(e)}")
        return False

def main():
    # 设置命令行参数
    parser = argparse.ArgumentParser(description='大学英语四级词汇表Excel转JSON工具')
    parser.add_argument('-i', '--input', required=True, help='输入Excel文件路径（例如：./cet4_vocab.xls）')
    parser.add_argument('-o', '--output', default='cet4_vocabulary.json', help='输出JSON文件路径（默认：./cet4_vocabulary.json）')
    
    args = parser.parse_args()
    
    # 验证输入文件是否存在
    if not os.path.exists(args.input):
        print(f"[ERROR] 输入文件不存在: {args.input}")
        return
    
    # 执行转换
    convert_cet4_vocab_to_json(args.input, args.output)

# 如果直接运行脚本，则执行主函数
if __name__ == "__main__":
    main()
