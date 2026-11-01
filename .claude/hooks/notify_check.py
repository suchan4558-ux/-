# Stop 훅: 사용자의 마지막 메시지 뒤로 PushNotification을 보냈는지 확인하고, 안 보냈으면 끝내지 못하게 막음.
# (사용자 요청: 답할 때마다 휴대폰 알림)
import sys, json

d = json.load(sys.stdin)
if d.get('stop_hook_active'):
    sys.exit(0)          # 한 번 막은 뒤에는 다시 막지 않음(무한 반복 방지)
path = d.get('transcript_path')
if not path:
    sys.exit(0)
try:
    lines = open(path, encoding='utf-8').read().splitlines()
except OSError:
    sys.exit(0)

sent = False
for l in reversed(lines):
    try:
        e = json.loads(l)
    except ValueError:
        continue
    m = e.get('message') or {}
    c = m.get('content')
    if e.get('type') == 'assistant' and isinstance(c, list):
        if any(x.get('type') == 'tool_use' and x.get('name') == 'PushNotification' for x in c):
            sent = True
    if e.get('type') == 'user':
        is_tool_result = isinstance(c, list) and any(x.get('type') == 'tool_result' for x in c)
        if not is_tool_result:
            break        # 사용자의 마지막 메시지에 닿음
if not sent:
    print(json.dumps({
        "decision": "block",
        "reason": "사용자 요청: 답마다 휴대폰 알림. PushNotification(status: proactive)으로 이번 답의 첫 줄 요지를 보낸 뒤, 다른 말 없이 끝낼 것."
    }, ensure_ascii=False))
sys.exit(0)
