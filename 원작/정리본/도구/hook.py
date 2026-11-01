# Claude Code 훅. .claude/settings.json에서 부름.
#  - 커밋하려 할 때(PreToolUse Bash): 새 줄 검사 + 장마다 검수 기록 확인. 걸리면 커밋을 막음.
#  - 갈래 파일을 Edit/Write로 고친 뒤(PostToolUse): 새 줄 검사. 걸리면 결과를 Claude에게 돌려줌.
import sys, json, os, re, subprocess
TOOL = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(TOOL)
d = json.load(sys.stdin)
ti = d.get('tool_input', {}) or {}
args = None
if d.get('hook_event_name') == 'PreToolUse' and d.get('tool_name') == 'Bash':
    if re.search(r'\bgit\b.*\bcommit\b', ti.get('command', '')):
        args = ['diff', '--commit']
elif d.get('hook_event_name') == 'PostToolUse':
    f = os.path.abspath(ti.get('file_path', '') or '')
    if os.path.dirname(f) == ROOT and re.match(r'\d+_', os.path.basename(f)):
        args = ['diff', f]
if args is None:
    sys.exit(0)
r = subprocess.run([sys.executable, os.path.join(TOOL, 'check.py')] + args, capture_output=True, text=True)
if r.returncode != 0:
    sys.stderr.write('정리본 검사에 걸렸습니다. 기준(원작 정리본 기준.md)을 다시 읽고 고치세요.\n' + r.stdout[-6000:])
    sys.exit(2)
sys.exit(0)
