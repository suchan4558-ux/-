#!/bin/sh
# 답이 끝나면 ntfy로 "답변 완료" 알림을 보냄. 누르면 그 세션이 열림.
# 같은 세션에서 10초 안에 또 불리면 보내지 않음(알림이 겹쳐 오는 것 막기).
id="${CLAUDE_CODE_REMOTE_SESSION_ID:-local}"
f="/tmp/ntfy_last_$id"
exec 9>>"$f"
flock -n 9 || exit 0
now=$(date +%s)
last=$(cat "/tmp/ntfy_time_$id" 2>/dev/null || echo 0)
[ $((now - last)) -lt 10 ] && exit 0
echo "$now" > "/tmp/ntfy_time_$id"
if [ "$CLAUDE_CODE_ACCOUNT_UUID" = "6a024a92-ecd1-43b1-8f70-fadaf0b744d7" ]; then name="Claude1"; else name="Claude2"; fi
curl -s -m 10 -H "Title: $name" \
  -H "Click: https://claude.ai/code/session_${id#cse_}" \
  -d '답변 완료' https://ntfy.sh/claude-noti-27e075ea79d3 >/dev/null 2>&1
exit 0
