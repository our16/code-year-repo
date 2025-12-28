# 临时脚本：批量替换print为logger

import re

# 读取文件
with open('src/generate_reports.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 替换规则
replacements = [
    (r'print\("\\n\[2/6\] 采集Git数据\.\.\."\)', 'logger.info("[2/6] 采集Git数据...")'),
    (r'print\("\\n   扫描项目: \{project\[\'name\'\]\}"\)', 'logger.info(f"扫描项目: {project[\'name\']}")'),
    (r'print\("   \[OK\] 完成: 找到.*条提交记录"\)', 'logger.info(f"   [OK] 完成: 找到 {len(project_data.get(\'commits\', []))} 条提交记录")'),
    (r'print\("   \[FAIL\] 失败:"\)', 'logger.error(f"   [FAIL] 失败: {str(e)}")'),
    (r'print\("\\n错误: 未能收集到任何数据"\)', 'logger.error("未能收集到任何数据")'),
    (r'print\("\\n   发现.*位作者"\)', 'logger.info(f"发现 {len(all_authors)} 位作者")'),
    (r'print\("\\n\[3/6\] 按作者分组数据\.\.\."\)', 'logger.info("[3/6] 按作者分组数据...")'),
    (r'print\("   -.*:.*次提交.*"\)', 'logger.info(f"   - {author_name}: {total_commits} 次提交{mapping_info}")'),
    (r'print\("\\n\[4/6\] 初始化LLM\.\.\."\)', 'logger.info("[4/6] 初始化LLM...")'),
    (r'print\("   使用LLM生成个性化文案"\)', 'logger.info("使用LLM生成个性化文案")'),
    (r'print\("   LLM初始化失败，使用预设模板"\)', 'logger.warning("LLM初始化失败，使用预设模板")'),
    (r'print\("   使用预设模板生成文案"\)', 'logger.info("使用预设模板生成文案")'),
    (r'print\("\\n\[5/6\] 生成JSON报告\.\.\."\)', 'logger.info("[5/6] 生成JSON报告...")'),
    (r'print\("   \[.*/.*\] 分析作者:"\)', 'logger.info(f"   [{idx}/{total_authors}] 分析作者: {author_name}")'),
    (r'print\("      警告: AI文案生成失败"\)', 'logger.warning(f"AI文案生成失败 - {str(e)}")'),
    (r'print\("      \[OK\] 报告已生成:"\)', 'logger.info(f"报告已生成: {json_filename}")'),
    (r'print\("\\n\[6/6\] 生成总索引文件\.\.\."\)', 'logger.info("[6/6] 生成总索引文件...")'),
    (r'print\("   \[OK\] 索引文件: report_index\.json"\)', 'logger.info("索引文件: report_index.json")'),
    (r'print\("\\n" + "=" \* 60\nprint\("\[SUCCESS\] JSON数据生成完成!"\nprint\("=" \* 60',
     'logger.info("=" * 60)\n    logger.info("[SUCCESS] JSON数据生成完成!")\n    logger.info("=" * 60'),
]

# 保存原文件
with open('src/generate_reports.py.bak', 'w', encoding='utf-8') as f:
    f.write(content)

print("已创建备份文件: src/generate_reports.py.bak")
print("请手动完成剩余的print替换")
