"""wxgzh-pipeline — WeChat 公众号 orchestration skill (orchestrator only).

One-line 发文：<选题> runs a fixed 6-stage pipeline over installed sub-skills
and creates a WeChat DRAFT. No formal publish / mass-send / schedule / delete
capability exists in this package.
"""

__version__ = "0.1.0-dev2-hotfix9R3"

STAGES = [
    "aihot",
    "super_writer",
    "zh_human_writing",
    "media_enrichment",
    "gzh_design",
    "wechat_draft",
]

# Execution/network modes:
#   offline_fixture - copy canned outputs (fast unit checks)
#   fake_live       - REAL orchestration machinery (agent handshake, real
#                     subprocess, real validators, receipt hashes) with fake
#                     sub-skills + fake WeChat client; NO real side effects
#   integration     - fake agent inputs + REAL installed media/gzh-design CLIs;
#                     WeChat is dry-run/audit only, with zero real side effects
#   live            - real agent + real installed sub-skills + real WeChat draft
NETWORK_MODES = ["offline_fixture", "fake_live", "integration", "live"]

# Capabilities that MUST NOT exist anywhere in this package (asserted by tests).
PROHIBITED_CAPABILITIES = ["freepublish", "mass_send", "schedule_publish", "delete_draft"]
FORMAL_PUBLISH = False
