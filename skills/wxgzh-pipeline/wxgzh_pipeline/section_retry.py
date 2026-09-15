"""77AK/OBS-388:单节回滚重试路径的分节/定位/重组装 helper。

背景(tjyl4w 生产实证):super_writer 阶段失败即整阶段重跑(agent 全部产物重生成,
wall 2354s 中真生成约 2 分钟,其余为 agent 自查等待)。本模块只做「失败节定位 →
重新组装 → 官方校验重跑」所需的文件级操作,不改任何校验语义:

- 分节口径与 super-writer 官方 split_sections(scripts/validate_article_length.py
  L175-201)同形:按 markdown 标题行分节、``` 围栏内不计标题;preamble 归首节
  (首节无标题行)。
- 组装是逐节原文字节拼接,不做「朴素 join」——朴素 join 会丢标题行/丢行尾换行。
  组装结果与拆分前逐字节相同的断言在测试里钉死(test_hf77ak_section_retry.py)。
- 本模块不写文章正文:正文由调用方给出的 driver(失败节重生成动作)写回,
  helper 只负责定位/读回/装配。

重试上限显式常量在 producers.SECTION_RETRY_MAX_ATTEMPTS(单一真源)。
"""
from __future__ import annotations

import re
from pathlib import Path

_HEADING_RE = re.compile(r"^(#{1,6})\s+(.+)$")

PREAMBLE_TITLE = "(preamble)"


class SectionRetry:
    """一个待重试节的执行上下文:分节、定位、读回、重组装。"""

    def __init__(self, article_path, header: str | None = None, index: int | None = None,
                 splitter=None):
        self.article_path = Path(article_path)
        self.header = header
        self.index = index
        self._splitter = splitter or split_sections
        self._sections: list[dict] | None = None
        self._original: list[dict] | None = None
        self.located_index: int | None = None

    # ---------- 分节 / 定位 ----------

    def _ensure_sections(self) -> list[dict]:
        if self._sections is None:
            raw = self._splitter(self.article_path.read_text(encoding="utf-8"))
            self._original = raw
            self._sections = [dict(s) for s in raw]
        return self._sections

    def locate(self) -> bool:
        """定位失败节:header 优先,其次 index(两者都空=首节);找不到返回 False。"""
        sections = self._ensure_sections()
        if self.header is not None:
            for i, s in enumerate(sections):
                if s["title"] == self.header:
                    self.located_index = i
                    return True
            return False
        if self.index is not None:
            if 0 <= self.index < len(sections):
                self.located_index = self.index
                return True
            return False
        self.located_index = 0 if sections else None
        return bool(sections)

    def section_text(self) -> str:
        """当前节原文(含标题行;sections 未加载时先加载)。"""
        self._ensure_sections()
        if self.located_index is None:
            raise ValueError("section not located yet: call locate() first")
        return self._sections[self.located_index]["text"]

    def rewrite_section(self, text: str) -> None:
        """用重生成后的节原文替换该节(标题行由调用方逐字保留)。"""
        self._ensure_sections()
        if self.located_index is None:
            raise ValueError("section not located yet: call locate() first")
        self._sections[self.located_index]["text"] = text

    # ---------- 重组装 / 写回 ----------

    def assembled_text(self) -> str:
        sections = self._ensure_sections()
        return "".join(s["text"] for s in sections)

    def unchanged(self) -> bool:
        """其余节逐字未变(以首次加载的原文为基准)。"""
        self._ensure_sections()
        assert self._original is not None
        for i, (cur, orig) in enumerate(zip(self._sections, self._original)):
            if i == self.located_index:
                continue
            if cur["text"] != orig["text"]:
                return False
        return True

    def other_section_texts(self) -> list[str]:
        """除目标节外的全部节原文(逐字,供测试钉住未变)。"""
        self._ensure_sections()
        return [s["text"] for i, s in enumerate(self._sections) if i != self.located_index]

    def write_back(self) -> bytes:
        """组装并写回文章(保留原行尾字节),返回写回后的字节。"""
        data = self.assembled_text().encode("utf-8")
        self.article_path.write_bytes(data)
        return data


# ---------- 显式分节 API(分节口径单一实现,SectionRetry 与调用方共用) ----------

def split_sections(article_text: str) -> list[dict]:
    """按 markdown 标题行分节(``` 围栏内不计标题),与官方 split_sections 同形。

    返回 [{"title": 标题文本, "text": 含标题行的整段原文}]。首节无标题行时
    title=PREAMBLE_TITLE。
    """
    lines = article_text.split("\n")
    sections: list[dict] = []
    current_title = PREAMBLE_TITLE
    title_pending: str | None = None        # 本节的标题行原文,尚无正文时挂起
    current_lines: list[str] = []
    in_fence = False

    def prime() -> None:
        """有正文行到来:把挂起的标题行并入本节正文。"""
        nonlocal title_pending
        if title_pending is not None:
            current_lines.append(title_pending)
            title_pending = None

    def flush(closed: bool) -> None:
        """把一个节定稿。closed=True 表示本节被下一个标题行关闭,其末行在原文中
        带换行(补回);空节(标题行后直接跟下一个标题行)只留标题行本身——补换行
        会多一字节。"""
        nonlocal current_lines, title_pending
        if closed:
            prime()
        if current_lines:
            sections.append({"title": current_title,
                             "text": _join(current_lines, closed)})
        elif title_pending is not None:
            sections.append({"title": current_title, "text": title_pending})
        current_lines = []
        title_pending = None

    for line in lines:
        if line.strip().startswith("```"):
            in_fence = not in_fence
            prime()
            current_lines.append(line)
            continue
        if in_fence:
            current_lines.append(line)
            continue
        m = _HEADING_RE.match(line)
        if m:
            flush(True)
            current_title = m.group(2).strip()
            title_pending = line
        else:
            prime()
            current_lines.append(line)
    # 末节:末行行尾换行原样保留(closed=False),保证 reassemble 与原文逐字节相同。
    flush(False)
    return sections


def _join(lines: list[str], trailing_newline: bool) -> str:
    """把节内行拼回原文片段。trailing_newline:本节的末行在原文中带换行(非末节)。"""
    if not lines:
        return ""
    return "\n".join(lines) + ("\n" if trailing_newline else "")


def reassemble(sections: list[dict]) -> str:
    return "".join(s["text"] for s in sections)


def reassemble_preserving_headings(original_text: str, sections: list[dict]) -> str:
    """组装后校验标题行逐字保留;不一致抛 ValueError(防朴素 join 丢标题行)。"""
    heading_re = re.compile(r"^(#{1,6})\s+(.+)$", re.M)
    if heading_re.findall(original_text) != heading_re.findall(reassemble(sections)):
        raise ValueError("reassembled article lost or changed heading lines")
    return reassemble(sections)
