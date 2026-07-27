"""wxgzh-pipeline — WeChat 公众号 orchestration skill (orchestrator only).

One-line 发文：<选题> runs a fixed 6-stage pipeline over installed sub-skills
and creates a WeChat DRAFT. No formal publish / mass-send / schedule / delete
capability exists in this package.
"""

__version__ = "0.1.0-dev1"

STAGES = [
    "aihot",
    "super_writer",
    "zh_human_writing",
    "media_enrichment",
    "gzh_design",
    "wechat_draft",
]

# Capabilities that MUST NOT exist anywhere in this package (asserted by tests).
PROHIBITED_CAPABILITIES = ["freepublish", "mass_send", "schedule_publish", "delete_draft"]
FORMAL_PUBLISH = False
