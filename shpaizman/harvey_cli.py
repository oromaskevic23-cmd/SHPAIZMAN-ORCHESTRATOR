"""Local-only HARVEY-pattern SHPAIZMAN scout queue CLI (zero network)."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from .business_cli import local_root
from .harvey_bridge import catalog, HarveyBridge, HarveyDenied


def main(argv=None):
    parser = argparse.ArgumentParser(description="SHPAIZMAN HARVEY-style offline planning")
    parser.add_argument("--data-dir", type=Path, default=local_root())
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("catalog", "status", "pause", "verify", "resume"):
        commands.add_parser(name)
    queue = commands.add_parser("enqueue")
    for name in ("agent", "provider", "task-type", "title", "source-url", "event-key"):
        queue.add_argument("--" + name, required=True)
    cycle = commands.add_parser("cycle")
    cycle.add_argument("--agent", required=True)
    task = commands.add_parser("task")
    task.add_argument("--id", required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "catalog":
            result = catalog()
        else:
            bridge = HarveyBridge(args.data_dir)
            if args.command == "status": result = bridge.status()
            elif args.command == "pause": result = bridge.set_enabled(False)
            elif args.command == "resume":
                # Local operator assertion, not cryptographic owner authentication.
                result = bridge.set_enabled(True, local_operator_ack=True)
            elif args.command == "verify": result = bridge.verify()
            elif args.command == "cycle": result = bridge.cycle(args.agent)
            elif args.command == "task": result = bridge.task(args.id)
            else:
                result = bridge.enqueue(agent=args.agent, provider=args.provider,
                    task_type=args.task_type, title=args.title,
                    source_url=args.source_url, event_key=args.event_key)
    except HarveyDenied as error:
        parser.exit(2, "BLOCKED: " + str(error) + "\n")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
