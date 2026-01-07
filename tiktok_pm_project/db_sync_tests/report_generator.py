import json
import os
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')

class ReportGenerator:
    def __init__(self, output_dir: str = "test_reports"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
    
    def generate_html_report(self, report_data: Dict[str, Any], filename: Optional[str] = None) -> str:
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"test_report_{timestamp}.html"
        
        filepath = os.path.join(self.output_dir, filename)
        
        html_content = self._generate_html_content(report_data)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return filepath
    
    def _generate_html_content(self, report_data: Dict[str, Any]) -> str:
        suite_name = report_data.get('suite_name', '测试报告')
        start_time = report_data.get('start_time', '')
        end_time = report_data.get('end_time', '')
        duration = report_data.get('duration', 0)
        total_tests = report_data.get('total_tests', 0)
        passed_tests = report_data.get('passed_tests', 0)
        failed_tests = report_data.get('failed_tests', 0)
        skipped_tests = report_data.get('skipped_tests', 0)
        success_rate = report_data.get('success_rate', 0)
        summary = report_data.get('summary', '')
        results = report_data.get('results', [])
        environment = report_data.get('environment', {})
        
        html = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{suite_name}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            background-color: #f5f5f5;
            padding: 20px;
        }}
        
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background-color: white;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            overflow: hidden;
        }}
        
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
        }}
        
        .header h1 {{
            font-size: 32px;
            margin-bottom: 10px;
        }}
        
        .header .meta {{
            font-size: 14px;
            opacity: 0.9;
        }}
        
        .summary {{
            padding: 30px;
            background-color: #f8f9fa;
            border-bottom: 1px solid #e9ecef;
        }}
        
        .summary-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }}
        
        .summary-card {{
            background-color: white;
            padding: 20px;
            border-radius: 6px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            text-align: center;
        }}
        
        .summary-card .value {{
            font-size: 36px;
            font-weight: bold;
            color: #667eea;
        }}
        
        .summary-card .label {{
            font-size: 14px;
            color: #6c757d;
            margin-top: 5px;
        }}
        
        .success-rate {{
            font-size: 48px;
            font-weight: bold;
            color: {self._get_success_rate_color(success_rate)};
        }}
        
        .content {{
            padding: 30px;
        }}
        
        .section {{
            margin-bottom: 30px;
        }}
        
        .section h2 {{
            font-size: 24px;
            margin-bottom: 15px;
            color: #495057;
            border-bottom: 2px solid #667eea;
            padding-bottom: 10px;
        }}
        
        .test-results {{
            display: grid;
            gap: 15px;
        }}
        
        .test-result {{
            background-color: white;
            border: 1px solid #dee2e6;
            border-radius: 6px;
            padding: 20px;
            transition: all 0.3s ease;
        }}
        
        .test-result:hover {{
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}
        
        .test-result.passed {{
            border-left: 4px solid #28a745;
        }}
        
        .test-result.failed {{
            border-left: 4px solid #dc3545;
        }}
        
        .test-result.skipped {{
            border-left: 4px solid #ffc107;
        }}
        
        .test-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 10px;
        }}
        
        .test-name {{
            font-size: 18px;
            font-weight: bold;
        }}
        
        .test-status {{
            padding: 5px 15px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: bold;
            text-transform: uppercase;
        }}
        
        .test-status.passed {{
            background-color: #d4edda;
            color: #155724;
        }}
        
        .test-status.failed {{
            background-color: #f8d7da;
            color: #721c24;
        }}
        
        .test-status.skipped {{
            background-color: #fff3cd;
            color: #856404;
        }}
        
        .test-details {{
            margin-top: 15px;
            padding-top: 15px;
            border-top: 1px solid #e9ecef;
        }}
        
        .test-duration {{
            color: #6c757d;
            font-size: 14px;
        }}
        
        .test-message {{
            margin-top: 10px;
            padding: 10px;
            background-color: #f8f9fa;
            border-radius: 4px;
            font-size: 14px;
        }}
        
        .test-errors {{
            margin-top: 10px;
        }}
        
        .error-item {{
            padding: 10px;
            background-color: #f8d7da;
            color: #721c24;
            border-radius: 4px;
            margin-top: 5px;
            font-size: 14px;
        }}
        
        .environment {{
            background-color: #f8f9fa;
            padding: 20px;
            border-radius: 6px;
        }}
        
        .environment-item {{
            display: flex;
            justify-content: space-between;
            padding: 8px 0;
            border-bottom: 1px solid #e9ecef;
        }}
        
        .environment-item:last-child {{
            border-bottom: none;
        }}
        
        .environment-key {{
            font-weight: bold;
            color: #495057;
        }}
        
        .environment-value {{
            color: #6c757d;
        }}
        
        .footer {{
            text-align: center;
            padding: 20px;
            background-color: #f8f9fa;
            color: #6c757d;
            font-size: 14px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{suite_name}</h1>
            <div class="meta">
                <p>开始时间: {start_time}</p>
                <p>结束时间: {end_time}</p>
                <p>总耗时: {duration:.2f}秒</p>
            </div>
        </div>
        
        <div class="summary">
            <h2>测试摘要</h2>
            <p>{summary}</p>
            <div class="summary-grid">
                <div class="summary-card">
                    <div class="value">{total_tests}</div>
                    <div class="label">总测试数</div>
                </div>
                <div class="summary-card">
                    <div class="value" style="color: #28a745;">{passed_tests}</div>
                    <div class="label">通过</div>
                </div>
                <div class="summary-card">
                    <div class="value" style="color: #dc3545;">{failed_tests}</div>
                    <div class="label">失败</div>
                </div>
                <div class="summary-card">
                    <div class="value" style="color: #ffc107;">{skipped_tests}</div>
                    <div class="label">跳过</div>
                </div>
                <div class="summary-card">
                    <div class="success-rate">{success_rate:.1f}%</div>
                    <div class="label">成功率</div>
                </div>
            </div>
        </div>
        
        <div class="content">
            <div class="section">
                <h2>环境信息</h2>
                <div class="environment">
                    {self._generate_environment_html(environment)}
                </div>
            </div>
            
            <div class="section">
                <h2>测试结果</h2>
                <div class="test-results">
                    {self._generate_test_results_html(results)}
                </div>
            </div>
        </div>
        
        <div class="footer">
            <p>报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
    </div>
</body>
</html>
"""
        
        return html
    
    def _get_success_rate_color(self, rate: float) -> str:
        if rate >= 80:
            return '#28a745'
        elif rate >= 50:
            return '#ffc107'
        else:
            return '#dc3545'
    
    def _generate_environment_html(self, environment: Dict[str, Any]) -> str:
        html = ""
        for key, value in environment.items():
            html += f"""
            <div class="environment-item">
                <span class="environment-key">{key}</span>
                <span class="environment-value">{value}</span>
            </div>
            """
        return html
    
    def _generate_test_results_html(self, results: List[Dict[str, Any]]) -> str:
        html = ""
        for result in results:
            status = result.get('status', 'unknown')
            test_name = result.get('test_name', '未知测试')
            duration = result.get('duration', 0)
            message = result.get('message', '')
            errors = result.get('errors', [])
            warnings = result.get('warnings', [])
            
            status_class = status.lower()
            
            html += f"""
            <div class="test-result {status_class}">
                <div class="test-header">
                    <div class="test-name">{test_name}</div>
                    <div class="test-status {status_class}">{status}</div>
                </div>
                <div class="test-duration">耗时: {duration:.2f}秒</div>
                """
            
            if message:
                html += f"""
                <div class="test-details">
                    <div class="test-message">{message}</div>
                """
            
            if errors:
                html += '<div class="test-errors">'
                for error in errors:
                    html += f'<div class="error-item">{error}</div>'
                html += '</div>'
            
            if warnings:
                html += '<div class="test-errors">'
                for warning in warnings:
                    html += f'<div class="error-item" style="background-color: #fff3cd; color: #856404;">警告: {warning}</div>'
                html += '</div>'
            
            if message or errors or warnings:
                html += '</div>'
            
            html += '</div>'
        
        return html
    
    def generate_json_report(self, report_data: Dict[str, Any], filename: Optional[str] = None) -> str:
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"test_report_{timestamp}.json"
        
        filepath = os.path.join(self.output_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, ensure_ascii=False, indent=2)
        
        return filepath
    
    def generate_markdown_report(self, report_data: Dict[str, Any], filename: Optional[str] = None) -> str:
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"test_report_{timestamp}.md"
        
        filepath = os.path.join(self.output_dir, filename)
        
        markdown_content = self._generate_markdown_content(report_data)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        
        return filepath
    
    def _generate_markdown_content(self, report_data: Dict[str, Any]) -> str:
        suite_name = report_data.get('suite_name', '测试报告')
        start_time = report_data.get('start_time', '')
        end_time = report_data.get('end_time', '')
        duration = report_data.get('duration', 0)
        total_tests = report_data.get('total_tests', 0)
        passed_tests = report_data.get('passed_tests', 0)
        failed_tests = report_data.get('failed_tests', 0)
        skipped_tests = report_data.get('skipped_tests', 0)
        success_rate = report_data.get('success_rate', 0)
        summary = report_data.get('summary', '')
        results = report_data.get('results', [])
        environment = report_data.get('environment', {})
        
        markdown = f"""# {suite_name}

## 测试摘要

{summary}

### 统计信息

| 指标 | 数值 |
|------|------|
| 总测试数 | {total_tests} |
| 通过 | {passed_tests} |
| 失败 | {failed_tests} |
| 跳过 | {skipped_tests} |
| 成功率 | {success_rate:.1f}% |

### 执行信息

| 项目 | 信息 |
|------|------|
| 开始时间 | {start_time} |
| 结束时间 | {end_time} |
| 总耗时 | {duration:.2f}秒 |

## 环境信息

"""
        
        for key, value in environment.items():
            markdown += f"- **{key}**: {value}\n"
        
        markdown += "\n## 测试结果\n\n"
        
        for result in results:
            status = result.get('status', 'unknown')
            test_name = result.get('test_name', '未知测试')
            duration = result.get('duration', 0)
            message = result.get('message', '')
            errors = result.get('errors', [])
            warnings = result.get('warnings', [])
            
            status_emoji = {
                'passed': '✅',
                'failed': '❌',
                'skipped': '⚠️'
            }.get(status.lower(), '❓')
            
            markdown += f"### {status_emoji} {test_name}\n\n"
            markdown += f"- **状态**: {status}\n"
            markdown += f"- **耗时**: {duration:.2f}秒\n"
            
            if message:
                markdown += f"- **信息**: {message}\n"
            
            if errors:
                markdown += "\n**错误**:\n"
                for error in errors:
                    markdown += f"- {error}\n"
            
            if warnings:
                markdown += "\n**警告**:\n"
                for warning in warnings:
                    markdown += f"- {warning}\n"
            
            markdown += "\n"
        
        markdown += f"\n---\n\n*报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n"
        
        return markdown
    
    def generate_charts(self, report_data: Dict[str, Any]) -> List[str]:
        chart_files = []
        
        results = report_data.get('results', [])
        
        if not results:
            return chart_files
        
        test_names = [r.get('test_name', '') for r in results]
        durations = [r.get('duration', 0) for r in results]
        
        fig, ax = plt.subplots(figsize=(12, 6))
        bars = ax.bar(range(len(test_names)), durations, color='#667eea')
        
        ax.set_xlabel('测试用例')
        ax.set_ylabel('耗时 (秒)')
        ax.set_title('测试用例执行时间')
        ax.set_xticks(range(len(test_names)))
        ax.set_xticklabels(test_names, rotation=45, ha='right')
        
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{height:.2f}s',
                   ha='center', va='bottom')
        
        plt.tight_layout()
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        chart_file = os.path.join(self.output_dir, f"test_duration_{timestamp}.png")
        plt.savefig(chart_file, dpi=300, bbox_inches='tight')
        plt.close()
        
        chart_files.append(chart_file)
        
        passed = report_data.get('passed_tests', 0)
        failed = report_data.get('failed_tests', 0)
        skipped = report_data.get('skipped_tests', 0)
        
        if passed + failed + skipped > 0:
            fig, ax = plt.subplots(figsize=(8, 8))
            labels = ['通过', '失败', '跳过']
            sizes = [passed, failed, skipped]
            colors = ['#28a745', '#dc3545', '#ffc107']
            explode = (0.1, 0, 0)
            
            ax.pie(sizes, explode=explode, labels=labels, colors=colors,
                  autopct='%1.1f%%', shadow=True, startangle=90)
            ax.set_title('测试结果分布')
            ax.axis('equal')
            
            plt.tight_layout()
            
            chart_file = os.path.join(self.output_dir, f"test_distribution_{timestamp}.png")
            plt.savefig(chart_file, dpi=300, bbox_inches='tight')
            plt.close()
            
            chart_files.append(chart_file)
        
        return chart_files
    
    def generate_all_reports(self, report_data: Dict[str, Any]) -> Dict[str, str]:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        html_file = self.generate_html_report(report_data, f"test_report_{timestamp}.html")
        json_file = self.generate_json_report(report_data, f"test_report_{timestamp}.json")
        markdown_file = self.generate_markdown_report(report_data, f"test_report_{timestamp}.md")
        chart_files = self.generate_charts(report_data)
        
        return {
            'html': html_file,
            'json': json_file,
            'markdown': markdown_file,
            'charts': chart_files
        }
