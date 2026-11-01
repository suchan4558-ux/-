#!/usr/bin/env python3
# Stop 훅: 이번 턴에 PushNotification을 보내지 않았으면 답을 끝내지 못하게 막는다.
import json, sys

data = json.load(sys.stdin)
if data.get("stop_hook_active"):
    sys.exit(0)  # 이미 한 번 막았으면 다시 막지 않음(무한 반복 방지)

entries = []
with open(data["transcript_path"], encoding="utf-8") as f:
    for line in f:
        try:
            entries.append(json.loads(line))
        except ValueError:
            pass

def is_user_prompt(e):
    if e.get("type") != "user" or e.get("isMeta"):
        return False
    c = e.get("message", {}).get("content")
    if isinstance(c, str):
        return True
    return any(b.get("type") == "text" for b in c or [] if isinstance(b, dict))

start = max((i for i, e in enumerate(entries) if is_user_prompt(e)), default=-1)
for e in entries[start + 1:]:
    if e.get("type") != "assistant":
        continue
    for b in e.get("message", {}).get("content") or []:
        if isinstance(b, dict) and b.get("type") == "tool_use" and b.get("name") == "PushNotification":
            sys.exit(0)

print(json.dumps({"decision": "block",
                  "reason": "이번 답에서 PushNotification으로 \"답변 완료\"를 아직 보내지 않았습니다. 보내고 끝내세요."},
                 ensure_ascii=False))
