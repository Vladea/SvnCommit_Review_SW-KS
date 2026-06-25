import re


def rule_review(project, rev, author, file_path, diff_text):
    issues = []

    def add(level, typ, desc, reason, suggestion):
        issues.append({
            'project_name': project, 'revision': rev, 'author': author,
            'level': level, 'issue_type': typ, 'file_path': file_path,
            'line_no': 'unknown', 'description': desc, 'reason': reason,
            'suggestion': suggestion, 'need_manual_check': 1, 'engine_type': 'rule'
        })

    for pat, level, desc in [
        ('<<<<<<<', 'P1', '发现疑似合并冲突开始标记'),
        ('>>>>>>>', 'P1', '发现疑似合并冲突结束标记'),
        ('=======', 'P3', '发现分隔符，需要确认是否为冲突残留或普通注释')
    ]:
        if pat in diff_text:
            add(level, 'merge_conflict', desc, f'diff 中包含 {pat}', '请确认是否为真实冲突标记。')

    if re.search(r'\bTODO\b|\bFIXME\b', diff_text, re.I):
        add('P4', 'style', '新增代码包含 TODO/FIXME', 'diff 中存在 TODO/FIXME', '建议补充 owner 或跟踪事项。')

    if re.search(r'\bprintf\s*\(|\bSystem\.out\.println\s*\(', diff_text):
        add('P3', 'debug', '可能存在临时调试输出', '新增代码包含直接打印语句', '建议使用统一日志接口。')

    if str(file_path).lower().endswith(('.c', '.h', '.cpp', '.hpp')) and 'memcpy' in diff_text \
            and not re.search(r'sizeof|ARRAY_SIZE|Length|Size', diff_text):
        add('P3', 'boundary', 'memcpy 使用需要确认长度边界', '未明显看到长度保护', '建议确认 buffer 长度。')

    return issues
