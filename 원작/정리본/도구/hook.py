# Claude Code 훅. .claude/settings.json에서 부름.
#  - 검수 기록(도구/검수/)은 검수 에이전트(geomsu)만 씀. 다른 쪽이 쓰려 하면 막음.
#  - 검수 에이전트는 검수 기록 밖의 파일을 고치지 못함.
#  - 커밋하려 할 때: 새 줄 검사 + 장마다 검수 기록(통과, 지문 일치) 확인. 걸리면 커밋을 막음.
#  - 갈래 파일을 Edit/Write로 고친 뒤: 새 줄 검사. 걸리면 결과를 돌려줌.
import sys, json, os, re, subprocess
TOOL = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(TOOL)
GEOMSU = os.path.join(TOOL, '검수')
REVIEWER = 'geomsu'

d = json.load(sys.stdin)
ev, tool = d.get('hook_event_name'), d.get('tool_name')
ti = d.get('tool_input', {}) or {}
is_reviewer = d.get('agent_type') == REVIEWER

def block(msg):
    sys.stderr.write(msg + '\n'); sys.exit(2)

def run_check(args):
    r = subprocess.run([sys.executable, os.path.join(TOOL, 'check.py')] + args, capture_output=True, text=True)
    if r.returncode != 0:
        block('정리본 검사에 걸렸습니다. 기준(원작 정리본 기준.md)을 다시 읽고 고치세요.\n' + r.stdout[-6000:] + r.stderr[-2000:])

WRITE_TOOLS = ('Write', 'Edit', 'MultiEdit', 'NotebookEdit')
WRITE_BASH = re.compile(r'>|\btee\b|\bsed\b[^|;&]*\s-i|\bcp\b|\bmv\b|\brm\b|\bpython|\bperl\b|\btruncate\b|\bdd\b|\bln\b|\binstall\b|\bgit\s+(checkout|restore|reset|stash|apply|am|cherry-pick|revert|merge|rebase|pull)\b')

if ev == 'PreToolUse':
    if tool in WRITE_TOOLS:
        f = os.path.abspath(ti.get('file_path', '') or ti.get('notebook_path', '') or '')
        in_g = f.startswith(GEOMSU + os.sep)
        if in_g and not is_reviewer:
            block('검수 기록은 검수 에이전트(geomsu)만 씁니다. 도구/검수_지시.md대로 검수를 맡기세요.')
        if is_reviewer and not in_g:
            block('검수 에이전트는 줄을 직접 고치지 않습니다. 도구/검수/ 안의 기록만 씁니다.')
    if tool == 'Bash':
        cmd = ti.get('command', '')
        if not is_reviewer and ('검수/' in cmd or '검수"' in cmd or "검수'" in cmd) and WRITE_BASH.search(cmd):
            block('검수 기록(도구/검수/)을 건드리는 명령은 검수 에이전트만 씁니다.')
        if is_reviewer and WRITE_BASH.search(cmd) and not re.fullmatch(r'\s*python3 [^;&|>]*check\.py (fingerprint|geomsu) [\d-]+\s*', cmd):
            block('검수 에이전트는 파일을 바꾸는 명령을 쓰지 않습니다. 기록은 Write로 도구/검수/에만 씁니다.')
        if re.search(r'\bgit\b.*\bcommit\b', cmd):
            run_check(['diff', '--commit'])
elif ev == 'PostToolUse' and tool in WRITE_TOOLS:
    f = os.path.abspath(ti.get('file_path', '') or '')
    if os.path.dirname(f) == ROOT and re.match(r'\d+_', os.path.basename(f)):
        run_check(['diff', f])
sys.exit(0)
