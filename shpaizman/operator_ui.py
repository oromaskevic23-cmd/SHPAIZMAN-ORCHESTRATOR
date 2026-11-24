"""SHPAIZMAN local Windows operator console. All work uses the actual runtime."""
import os
from pathlib import Path
import threading
import time
import tkinter as tk
from tkinter import ttk, messagebox
from .runtime import Runtime, ROLES

def main():
    root = tk.Tk()
    root.title("SHPAIZMAN | Local AI Operator")
    root.geometry("1000x720")
    root.minsize(760, 520)
    data = Path(os.environ.get("LOCALAPPDATA") or Path.home()) / "SHPAIZMAN" / "runtime"
    runtime = Runtime(data)
    model = tk.StringVar(value="qwen2.5:3b")
    agent = tk.StringVar(value="bitrix24")
    health = tk.StringVar()
    stop_signal = threading.Event()
    worker = None
    worker_failure = None
    closing = False

    frame = ttk.Frame(root, padding=16)
    frame.pack(fill="both", expand=True)
    ttk.Label(frame, text="SHPAIZMAN ORCHESTRATOR", font=("Segoe UI", 20, "bold")).pack(anchor="w")
    ttk.Label(frame, text="Local AI · 10 specialist roles · Drafts require human review").pack(anchor="w", pady=(0,12))
    controls = ttk.Frame(frame)
    controls.pack(fill="x")
    ttk.Label(controls, text="Ollama model").pack(side="left")
    model_input = ttk.Entry(controls, textvariable=model, width=25)
    model_input.pack(side="left", padx=8)
    def loop(selected):
        nonlocal worker_failure
        try:
            while not stop_signal.is_set():
                if not runtime.once(selected):
                    stop_signal.wait(2)
        except Exception as exc:
            worker_failure = type(exc).__name__
            try:
                runtime.set_enabled(False)
            except Exception:
                pass
    def start():
        nonlocal worker, worker_failure
        if worker is not None and worker.is_alive():
            return
        if not model.get().strip():
            messagebox.showerror("Model required", "Enter an installed local Ollama model.")
            return
        try:
            runtime.set_enabled(True)
        except Exception as exc:
            messagebox.showerror("Start failed", type(exc).__name__)
            return
        worker_failure = None
        stop_signal.clear()
        worker = threading.Thread(target=loop, args=(model.get().strip(),), daemon=True)
        worker.start()
        start_button.configure(state="disabled")
        model_input.configure(state="disabled")
    def stop():
        stop_signal.set()
        try:
            runtime.set_enabled(False)
        except Exception as exc:
            messagebox.showerror("STOP could not be confirmed", type(exc).__name__)
            return False
        return True
    start_button = ttk.Button(controls,text="Start worker",command=start)
    start_button.pack(side="left",padx=4)
    ttk.Button(controls,text="STOP",command=stop).pack(side="left",padx=4)
    ttk.Label(frame,textvariable=health).pack(anchor="w",pady=10)
    ttk.Label(frame,text="Specialist role").pack(anchor="w")
    ttk.Combobox(frame,textvariable=agent,values=list(ROLES),state="readonly").pack(fill="x")
    ttk.Label(frame,text="Task (do not enter credentials or unnecessary personal data)").pack(anchor="w",pady=(8,0))
    task = tk.Text(frame,height=5,wrap="word")
    task.pack(fill="x")
    def submit():
        try:
            runtime.submit(agent.get(),task.get("1.0","end-1c"))
        except Exception as exc:
            messagebox.showerror("Task rejected",str(exc))
            return
        task.delete("1.0","end")
    ttk.Button(frame,text="Queue real AI task",command=submit).pack(anchor="w",pady=8)
    table = ttk.Treeview(frame,columns=("agent","state","model"),show="headings",height=7)
    for key in ("agent","state","model"):
        table.heading(key,text=key.title())
        table.column(key,width=150)
    table.pack(fill="both",expand=True)
    output = tk.Text(frame,height=8,wrap="word",state="disabled")
    output.pack(fill="both",expand=True,pady=(8,0))
    def show(_event=None):
        selected=table.selection()
        if not selected:
            return
        try:
            row=runtime.show(selected[0])
            value="State: "+row["state"]+"\n"+(row["output"] or row["error"] or "No result yet.")
        except Exception as exc:
            value="Read failed: "+type(exc).__name__
        output.configure(state="normal")
        output.delete("1.0","end")
        output.insert("1.0",value)
        output.configure(state="disabled")
    table.bind("<<TreeviewSelect>>",show)
    def refresh():
        if closing:
            return
        try:
            state=runtime.status()
            alive=worker is not None and worker.is_alive()
            health.set(("Processing enabled" if state["enabled"] else "STOPPED")+
                       " | Window worker: "+("running" if alive else "not running")+
                       " | External integrations: 0 verified"+
                       (" | Worker error: "+worker_failure if worker_failure else ""))
            if not alive:
                start_button.configure(state="normal")
                model_input.configure(state="normal")
            with runtime.db() as c:
                rows=c.execute("SELECT id,agent,state,model FROM jobs ORDER BY created DESC LIMIT 200").fetchall()
            ids={r["id"] for r in rows}
            for item in table.get_children():
                if item not in ids:
                    table.delete(item)
            for index,r in enumerate(rows):
                values=(r["agent"],r["state"],r["model"] or "")
                if table.exists(r["id"]):
                    table.item(r["id"],values=values)
                    table.move(r["id"],"",index)
                else:
                    table.insert("",index,iid=r["id"],values=values)
            show()
        except Exception as exc:
            health.set("Status unavailable: "+type(exc).__name__)
        root.after(1500,refresh)
    def close():
        nonlocal closing
        if stop():
            closing=True
            root.destroy()
    root.protocol("WM_DELETE_WINDOW",close)
    refresh()
    root.mainloop()

if __name__=="__main__":
    main()
