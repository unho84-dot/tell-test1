 (cd "$(git rev-parse --show-toplevel)" && git apply --3way <<'EOF' 
diff --git a/scheduler.py b/scheduler.py
new file mode 100644
index 0000000000000000000000000000000000000000..40a283abb80eb69957100cb103242be5f5b6b840
--- /dev/null
+++ b/scheduler.py
@@ -0,0 +1,18 @@
+import threading
+from datetime import datetime
+from zoneinfo import ZoneInfo
+from typing import Callable, Any, Tuple
+
+ASIA_SEOUL = ZoneInfo("Asia/Seoul")
+
+
+def parse_schedule_time(time_text: str) -> datetime:
+    return datetime.strptime(time_text, "%Y-%m-%d %H:%M").replace(tzinfo=ASIA_SEOUL)
+
+
+def schedule_send(target_time: datetime, func: Callable, args: Tuple[Any, ...] = ()) -> threading.Timer:
+    now = datetime.now(ASIA_SEOUL)
+    delay_seconds = max((target_time - now).total_seconds(), 0)
+    timer = threading.Timer(delay_seconds, func, args=args)
+    timer.start()
+    return timer
 
EOF
)
