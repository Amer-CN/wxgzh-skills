"""Supported CLI for writing a live agent-handshake ACK."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .agent_handshake import write_ack_from_request


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        prog="wxgzh-pipeline-ack",
        description="Write agent_handshake.json from an existing handshake request.",
    )
    parser.add_argument("--stage-dir", required=True,
                        help="Stage directory containing agent_handshake_request.json")
    parser.add_argument("--agent-id", default="agent", help="Identity recorded in the ACK")
    args = parser.parse_args(argv)
    try:
        ack = write_ack_from_request(Path(args.stage_dir), agent_id=args.agent_id)
    except (OSError, ValueError, TypeError) as exc:
        print(json.dumps({"status": "ACK_REJECTED", "error": str(exc)},
                         ensure_ascii=False, indent=2), file=sys.stderr)
        return 1
    print(json.dumps(ack, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
