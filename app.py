import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, simpledialog
from typing import Callable, List, Optional

from scheduler import parse_schedule_time, schedule_send
from sender import send_messages
from utils import ensure_recipient_limit, load_recipients_from_csv, parse_chat_ids

LOG_PATH = "send_log.csv"


class TelegramSenderApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Telegram Sender (MTProto)")
        self.root.configure(bg="#bfbfbf")
        self.recipients: List[str] = []
        self.message_slots: List[dict] = []
        self.phone_number: Optional[str] = None

        self._build_layout()

    def _build_layout(self) -> None:
        main_frame = tk.Frame(self.root, bg="#bfbfbf")
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        left_frame = tk.Frame(main_frame, bg="#bfbfbf")
        left_frame.pack(side="left", fill="both", expand=True)

        right_frame = tk.Frame(main_frame, bg="#bfbfbf")
        right_frame.pack(side="right", fill="y", padx=(10, 0))

        self._build_credentials_section(left_frame)
        self._build_message_slots(left_frame)
        self._build_recipient_section(right_frame)

    def _build_credentials_section(self, parent: tk.Widget) -> None:
        frame = tk.LabelFrame(parent, text="계정 정보", padx=10, pady=10, bg="#bfbfbf")
        frame.pack(fill="x", pady=(0, 10))

        tk.Label(frame, text="api_id", bg="#bfbfbf").grid(row=0, column=0, sticky="w", padx=(0, 5))
        self.api_id_entry = tk.Entry(frame, width=25)
        self.api_id_entry.grid(row=0, column=1, sticky="w")

        tk.Label(frame, text="api_hash", bg="#bfbfbf").grid(row=1, column=0, sticky="w", padx=(0, 5), pady=(5, 0))
        self.api_hash_entry = tk.Entry(frame, width=25)
        self.api_hash_entry.grid(row=1, column=1, sticky="w", pady=(5, 0))

        tk.Label(frame, text="2FA PW", bg="#bfbfbf").grid(row=2, column=0, sticky="w", padx=(0, 5), pady=(5, 0))
        self.password_entry = tk.Entry(frame, width=25, show="*")
        self.password_entry.grid(row=2, column=1, sticky="w", pady=(5, 0))

    def _build_message_slots(self, parent: tk.Widget) -> None:
        slots_frame = tk.Frame(parent, bg="#bfbfbf")
        slots_frame.pack(fill="both", expand=True)

        for index in range(1, 7):
            slot_frame = tk.Frame(slots_frame, bg="#bfbfbf", pady=4)
            slot_frame.pack(fill="x")

            tk.Label(slot_frame, text=f"{index} 전송메시지", bg="#bfbfbf").grid(row=0, column=0, sticky="w")
            message_entry = tk.Entry(slot_frame, width=45)
            message_entry.grid(row=0, column=1, padx=5, sticky="w")
            send_button = tk.Button(
                slot_frame,
                text="전송",
                command=lambda idx=index: self.handle_send_slot(idx),
                width=6,
            )
            send_button.grid(row=0, column=2, padx=5)

            tk.Label(slot_frame, text="전송시간", bg="#bfbfbf").grid(row=1, column=0, sticky="w", pady=(4, 0))
            time_entry = tk.Entry(slot_frame, width=30)
            time_entry.insert(0, "YYYY-MM-DD HH:MM")
            time_entry.grid(row=1, column=1, padx=5, sticky="w", pady=(4, 0))

            self.message_slots.append(
                {
                    "message_entry": message_entry,
                    "time_entry": time_entry,
                }
            )

    def _build_recipient_section(self, parent: tk.Widget) -> None:
        frame = tk.LabelFrame(parent, text="전송대상", padx=10, pady=10, bg="#bfbfbf")
        frame.pack(fill="both", expand=True)

        tk.Button(frame, text="recipients.csv 불러오기", command=self.load_csv).pack(anchor="w")
        tk.Label(frame, text="대상 chat_id 또는 username (줄바꿈)", bg="#bfbfbf").pack(anchor="w", pady=(5, 0))
        self.recipient_text = scrolledtext.ScrolledText(frame, height=20, width=25)
        self.recipient_text.pack(fill="both", expand=True)

    def load_csv(self) -> None:
        csv_path = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
        if not csv_path:
            return
        try:
            loaded = load_recipients_from_csv(csv_path)
        except Exception as exc:  # pragma: no cover - user feedback path
            messagebox.showerror("CSV Error", str(exc))
            return
        self.recipients = loaded
        messagebox.showinfo("Recipients loaded", f"Loaded {len(loaded)} chat_ids from file.")

    def _collect_recipients(self) -> List[str]:
        from_text = parse_chat_ids(self.recipient_text.get("1.0", tk.END))
        combined = self.recipients + from_text
        unique = list(dict.fromkeys(combined))  # preserve order and remove duplicates
        return unique

    def _validate(self, recipients: List[str], message: str) -> bool:
        if not recipients:
            messagebox.showwarning("Recipients", "Please load or paste at least one chat_id.")
            return False
        within_limit, count = ensure_recipient_limit(recipients)
        if not within_limit:
            messagebox.showwarning("Recipients", f"Maximum of 50 recipients allowed (current: {count}).")
            return False
        if not message.strip():
            messagebox.showwarning("Message", "Please enter a message to send.")
            return False
        return True

    def _validate_credentials(self) -> Optional[dict]:
        api_id_text = self.api_id_entry.get().strip()
        api_hash = self.api_hash_entry.get().strip()
        password = self.password_entry.get().strip() or None
        if not api_id_text.isdigit():
            messagebox.showwarning("계정 정보", "api_id는 숫자여야 합니다.")
            return None
        if not api_hash:
            messagebox.showwarning("계정 정보", "api_hash를 입력하세요.")
            return None
        return {
            "api_id": int(api_id_text),
            "api_hash": api_hash,
            "password": password,
        }

    def _get_phone_number(self) -> Optional[str]:
        if self.phone_number:
            return self.phone_number
        phone = simpledialog.askstring("전화번호", "Telegram 계정 전화번호를 입력하세요 (예: +82...)", parent=self.root)
        if not phone:
            return None
        self.phone_number = phone.strip()
        return self.phone_number

    def _get_code_callback(self) -> Callable[[], str]:
        def _callback() -> str:
            code = simpledialog.askstring("인증 코드", "Telegram에서 받은 인증 코드를 입력하세요.", parent=self.root)
            return code.strip() if code else ""

        return _callback

    def _send(self, recipients: List[str], message: str) -> None:
        credentials = self._validate_credentials()
        if not credentials:
            return
        phone = self._get_phone_number()
        if not phone:
            messagebox.showwarning("계정 정보", "전화번호가 필요합니다.")
            return
        try:
            results = send_messages(
                api_id=credentials["api_id"],
                api_hash=credentials["api_hash"],
                phone_number=phone,
                password=credentials["password"],
                recipients=recipients,
                message=message,
                log_path=LOG_PATH,
                code_callback=self._get_code_callback(),
            )
        except Exception as exc:  # pragma: no cover - user feedback path
            messagebox.showerror("Send Error", str(exc))
            return
        success = sum(1 for _, status, _ in results if status == "success")
        failure = len(results) - success
        messagebox.showinfo("Done", f"Sent: {success}\nFailed: {failure}")

    def handle_send_slot(self, index: int) -> None:
        slot = self.message_slots[index - 1]
        recipients = self._collect_recipients()
        message = slot["message_entry"].get()
        if not self._validate(recipients, message):
            return
        time_text = slot["time_entry"].get().strip()
        if not time_text or time_text == "YYYY-MM-DD HH:MM":
            self._send(recipients, message)
            return
        try:
            target_time = parse_schedule_time(time_text)
        except Exception as exc:
            messagebox.showerror("Schedule", f"Invalid time format: {exc}")
            return

        def job():
            self._send(recipients, message)

        schedule_send(target_time, job)
        messagebox.showinfo("Schedule", f"Message scheduled for {target_time} (Asia/Seoul)")


def main() -> None:
    root = tk.Tk()
    app = TelegramSenderApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
