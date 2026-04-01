import os
import re

def analyze_files():
    patterns = {
        'TODO/FIXME': [r'(?i)\btodo\b', r'(?i)\bfixme\b'],
        'Missing Logic': [r'NotImplementedError', r'NotImplemented', r'^\s*pass\s*$', r'^\s*\.\.\.\s*$'],
        'Mock/Simulate/Dummy': [r'(?i)\bmock\b', r'(?i)\bdummy\b', r'(?i)\bfake\b', r'(?i)\bsimulate\b', r'(?i)\bsimulation\b'],
        'Placeholder': [r'(?i)\bplaceholder\b'],
        'Tricks/Hacks': [r'(?i)\bhack\b', r'(?i)\btrick\b', r'(?i)\bworkaround\b'],
        'Intro/Fluff': [r'(?i)introduction', r'(?i)fluff', r'(?i)boilerplate']
    }

    # Flatten patterns for easy matching
    all_patterns = []
    for category, pat_list in patterns.items():
        all_patterns.extend([(re.compile(p), category) for p in pat_list])

    results = []
    total_files = 0
    files_with_issues = 0
    total_lines = 0
    total_issue_lines = 0

    for root, _, files in os.walk('.'):
        for file in files:
            if file.endswith('.py') and file not in ['generate_report.py', 'fluff_analyzer.py']:
                filepath = os.path.join(root, file)
                total_files += 1
                has_issue = False
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                        total_lines += len(lines)
                        file_results = []
                        for i, line in enumerate(lines):
                            for regex, category in all_patterns:
                                if regex.search(line):
                                    file_results.append(f"  - Line {i+1} ({category}): {line.strip()}")
                                    has_issue = True
                                    total_issue_lines += 1
                                    break
                        if file_results:
                            results.append(f"File: {filepath}")
                            results.extend(file_results)
                            files_with_issues += 1
                except Exception as e:
                    print(f"Error reading {filepath}: {e}")

    output_lines = []
    output_lines.extend(results)

    output_lines.append("\n--- Conclusion ---")

    if total_lines > 0:
        percentage = (total_issue_lines / total_lines) * 100
    else:
        percentage = 0

    output_lines.append(f"Total Python Files Analyzed: {total_files}")
    output_lines.append(f"Files Containing Identified Elements: {files_with_issues}")
    output_lines.append(f"Total Lines of Code: {total_lines}")
    output_lines.append(f"Total Lines with Identified Elements: {total_issue_lines}")
    output_lines.append(f"Percentage of Codebase Affected: {percentage:.2f}%")

    with open('report.txt', 'w', encoding='utf-8') as f:
        f.write('\n'.join(output_lines))

if __name__ == '__main__':
    analyze_files()
