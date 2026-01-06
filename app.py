import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
from typing import List

from utils import (
    ensure_recipient_limit,
    load_bot_token,
    load_recipients_from_csv,
    parse_chat_ids,
)
from sender import send_messages, send_test_message
from scheduler import parse_schedule_time, schedule_send

LOG_PATH = "send_log.csv"


class TelegramSenderApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Telegram Sender")
        self.recipients: List[str] = []

        self._build_recipient_section()
        self._build_message_section()
        self._build_schedule_section()
        self._build_buttons()

    def _build_recipient_section(self) -> None:
        frame = tk.LabelFrame(self.root, text="Recipients", padx=10, pady=10)
        frame.pack(fill="x", padx=10, pady=5)

        tk.Button(frame, text="Load recipients.csv", command=self.load_csv).pack(anchor="w")

        tk.Label(frame, text="Or paste chat_ids (one per line):").pack(anchor="w", pady=(5, 0))
        self.recipient_text = scrolledtext.ScrolledText(frame, height=5)
        self.recipient_text.pack(fill="both", expand=True)

    def _build_message_section(self) -> None:
        frame = tk.LabelFrame(self.root, text="Message", padx=10, pady=10)
        frame.pack(fill="both", padx=10, pady=5)

        self.message_text = scrolledtext.ScrolledText(frame, height=8)
        self.message_text.pack(fill="both", expand=True)

    def _build_schedule_section(self) -> None:
        frame = tk.LabelFrame(self.root, text="Schedule", padx=10, pady=10)
        frame.pack(fill="x", padx=10, pady=5)

        self.schedule_entry = tk.Entry(frame)
        self.schedule_entry.insert(0, "YYYY-MM-DD HH:MM (Asia/Seoul)")
        self.schedule_entry.pack(fill="x")

    def _build_buttons(self) -> None:
        frame = tk.Frame(self.root)
        frame.pack(fill="x", padx=10, pady=10)

        tk.Label(frame, text="Test chat_id:").grid(row=0, column=0, sticky="w")
        self.test_chat_id_entry = tk.Entry(frame)
        self.test_chat_id_entry.grid(row=0, column=1, padx=5, pady=5)

        tk.Button(frame, text="테스트 발송", command=self.handle_test_send).grid(row=0, column=2, padx=5)
        tk.Button(frame, text="즉시 발송", command=self.handle_immediate_send).grid(row=0, column=3, padx=5)
        tk.Button(frame, text="예약 발송", command=self.handle_schedule_send).grid(row=0, column=4, padx=5)

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

    def _send(self, recipients: List[str], message: str) -> None:
        try:
            token = load_bot_token()
            results = send_messages(token, recipients, message, log_path=LOG_PATH)
        except Exception as exc:  # pragma: no cover - user feedback path
            messagebox.showerror("Send Error", str(exc))
            return
        success = sum(1 for _, status, _ in results if status == "success")
        failure = len(results) - success
        messagebox.showinfo("Done", f"Sent: {success}\nFailed: {failure}")

    def handle_immediate_send(self) -> None:
        recipients = self._collect_recipients()
        message = self.message_text.get("1.0", tk.END)
        if not self._validate(recipients, message):
            return
        self._send(recipients, message)

    def handle_test_send(self) -> None:
        chat_id = self.test_chat_id_entry.get().strip()
        message = self.message_text.get("1.0", tk.END)
        if not chat_id:
            messagebox.showwarning("Test", "Please enter your chat_id for testing.")
            return
        if not message.strip():
            messagebox.showwarning("Message", "Please enter a message to send.")
            return
        try:
            token = load_bot_token()
            chat_id, status, error = send_test_message(token, chat_id, message, log_path=LOG_PATH)
            if status == "success":
                messagebox.showinfo("Test", "Test message sent successfully.")
            else:
                messagebox.showerror("Test", f"Failed: {error}")
        except Exception as exc:  # pragma: no cover - user feedback path
            messagebox.showerror("Test", str(exc))

    def handle_schedule_send(self) -> None:
        time_text = self.schedule_entry.get().strip()
        try:
            target_time = parse_schedule_time(time_text)
        except Exception as exc:
            messagebox.showerror("Schedule", f"Invalid time format: {exc}")
            return
        recipients = self._collect_recipients()
        message = self.message_text.get("1.0", tk.END)
        if not self._validate(recipients, message):
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
