"""
生成测试报告
"""
import json
import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 读取JSON结果文件
result_files = [f for f in os.listdir('.') if f.startswith('emotion_test_results_') and f.endswith('.json')]

if not result_files:
    print("未找到测试结果文件")
    sys.exit(1)

# 使用最新的结果文件
latest_file = max(result_files, key=lambda x: os.path.getctime(x))
print(f"读取测试结果文件: {latest_file}")

with open(latest_file, 'r', encoding='utf-8') as f:
    data = json.load(f)

results = data['results']

# 生成报告
report_lines = []
report_lines.append("="*80)
report_lines.append("对话功能与情感模块集成测试报告")
report_lines.append("="*80)
report_lines.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
report_lines.append(f"测试用例总数: {len(results)}")

# 统计结果
emotion_match_count = sum(1 for r in results if r['emotion_match'])
intensity_match_count = sum(1 for r in results if r['intensity_match'])
perfect_match_count = sum(1 for r in results if r['emotion_match'] and r['intensity_match'])

report_lines.append(f"\n统计结果:")
report_lines.append(f"  情感匹配: {emotion_match_count}/{len(results)} ({emotion_match_count/len(results)*100:.1f}%)")
report_lines.append(f"  强度匹配: {intensity_match_count}/{len(results)} ({intensity_match_count/len(results)*100:.1f}%)")
report_lines.append(f"  完全匹配: {perfect_match_count}/{len(results)} ({perfect_match_count/len(results)*100:.1f}%)")

# 按情感类型分组统计
report_lines.append(f"\n按情感类型统计:")
emotion_groups = {}
for result in results:
    emotion = result['expected_emotion']
    if emotion not in emotion_groups:
        emotion_groups[emotion] = {'total': 0, 'matched': 0}
    emotion_groups[emotion]['total'] += 1
    if result['emotion_match']:
        emotion_groups[emotion]['matched'] += 1

for emotion, stats in sorted(emotion_groups.items()):
    rate = stats['matched'] / stats['total'] * 100 if stats['total'] > 0 else 0
    report_lines.append(f"  {emotion}: {stats['matched']}/{stats['total']} ({rate:.1f}%)")

# 详细结果
report_lines.append(f"\n详细测试结果:")
report_lines.append("-"*80)

for result in results:
    status = "通过" if (result['emotion_match'] and result['intensity_match']) else "失败"
    report_lines.append(f"\n[{status}] {result['test_name']}")
    report_lines.append(f"  输入: {result['user_input']}")
    report_lines.append(f"  预期: {result['expected_emotion']} ({result['expected_intensity']})")
    report_lines.append(f"  实际: {result['detected_emotion']} ({result['detected_intensity']})")
    report_lines.append(f"  Live2D: {result['live2d_expression']} / {result['live2d_motion']}")
    if result['issues']:
        report_lines.append(f"  问题: {'; '.join(result['issues'])}")

# 失败用例汇总
failed_tests = [r for r in results if not (r['emotion_match'] and r['intensity_match'])]
if failed_tests:
    report_lines.append(f"\n\n失败用例汇总:")
    report_lines.append("-"*80)
    for result in failed_tests:
        report_lines.append(f"\n* {result['test_name']}")
        report_lines.append(f"  输入: {result['user_input']}")
        report_lines.append(f"  预期: {result['expected_emotion']} ({result['expected_intensity']})")
        report_lines.append(f"  实际: {result['detected_emotion']} ({result['detected_intensity']})")
        report_lines.append(f"  Live2D: {result['live2d_expression']} / {result['live2d_motion']}")
        report_lines.append(f"  问题: {'; '.join(result['issues'])}")

# 建议
report_lines.append(f"\n\n改进建议:")
report_lines.append("-"*80)

# 分析失败的情感类型
failed_emotions = {}
for result in failed_tests:
    emotion = result['expected_emotion']
    if emotion not in failed_emotions:
        failed_emotions[emotion] = 0
    failed_emotions[emotion] += 1

if failed_emotions:
    report_lines.append("需要重点优化的情感识别:")
    for emotion, count in sorted(failed_emotions.items(), key=lambda x: x[1], reverse=True):
        report_lines.append(f"  - {emotion}: {count}个测试失败")
    
    report_lines.append("\n建议调整:")
    report_lines.append("  1. 针对失败率高的情感类型，优化提示词(prompt)")
    report_lines.append("  2. 调整情感-动作映射规则")
    report_lines.append("  3. 考虑增加更多训练样本")
    report_lines.append("  4. 检查LLM模型对该情感类型的识别能力")
else:
    report_lines.append("所有测试通过！系统运行良好。")

report_lines.append("\n" + "="*80)

# 保存报告
report_text = '\n'.join(report_lines)
print(report_text)

report_filename = f"emotion_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
with open(report_filename, 'w', encoding='utf-8') as f:
    f.write(report_text)

print(f"\n报告已保存: {report_filename}")
