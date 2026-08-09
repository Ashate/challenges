#!/usr/bin/env python3
"""
遍历仓库中所有 benchmark.json（以及同目录下的 benchmark.yaml，如果存在多 flag 定义），
将其中的 description / hint 字段翻译成中文并写回。

幂等设计:
  - 每个文件写入一个 "i18n" 元数据块，记录英文原文及其 sha256:
        "i18n": {
            "description": {"en": "...", "en_sha256": "..."},
            "hint":        {"en": "...", "en_sha256": "..."}
        }
  - 下次运行时，如果当前字段内容的 hash 命中 i18n 里记录的 en_sha256，
    说明这份内容已经是"我们翻译产出的中文"，直接跳过，不会重复调用 API。
  - 如果 i18n 里没有记录，或者当前内容的 hash 对不上任何已知状态，
    则视为"新的/被上游更新过的英文原文"，重新翻译并更新 i18n 记录。

用法:
  python scripts/translate_challenges.py --root . [--dry-run] [--model deepseek-chat]

依赖:
  pip install openai pyyaml
环境变量:
  DEEPSEEK_API_KEY 必须设置
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
from pathlib import Path

import yaml
from openai import OpenAI, APIError, APIStatusError

DEEPSEEK_BASE_URL = "https://api.deepseek.com"

TRANSLATE_SYSTEM_PROMPT = (
    "你是一名专业的安全/CTF 题目文本译者。任务：把给定的英文文本忠实地翻译成简体中文。\n"
    "严格规则：\n"
    "1. 只输出翻译结果本身，不要加任何前后缀、解释、引号或 Markdown 代码块标记。\n"
    "2. 保留所有代码片段、命令、文件名、URL、变量名、占位符（如 {xxx}）、Markdown 语法不翻译，原样保留。\n"
    "3. 不要添加、删减或“剧透”原文没有的漏洞细节/解题步骤，只做语言转换。\n"
    "4. 专业术语和专有名词一律保留英文原文，不要翻译、不要音译、不要加中文括注。\n"
    "   包括但不限于：技术名词（SQL injection, XSS, SSRF, deserialization, buffer overflow, "
    "race condition, JWT, RCE 等）、协议/标准名（HTTP, OAuth, TLS 等）、编程语言/框架/库名"
    "（Python, Flask, Django, React 等）、产品/软件/公司名（Docker, Redis, Nginx, GitHub 等）、"
    "人名、CVE 编号、flag 一词本身。这些词直接原样嵌入中文句子中，其余部分正常翻译成中文。\n"
    "5. 如果原文本身是空字符串，直接原样返回空字符串。"
)


def sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


class Translator:
    def __init__(self, model: str, dry_run: bool = False):
        self.model = model
        self.dry_run = dry_run
        self.client = None if dry_run else OpenAI(
            api_key=os.environ.get("DEEPSEEK_API_KEY"),
            base_url=DEEPSEEK_BASE_URL,
        )
        self._cache: dict[str, str] = {}

    def translate(self, text: str) -> str:
        if not text.strip():
            return text
        if text in self._cache:
            return self._cache[text]
        if self.dry_run:
            translated = f"[DRY-RUN 待翻译] {text}"
        else:
            translated = self._call_api(text)
        self._cache[text] = translated
        return translated

    def _call_api(self, text: str, retries: int = 3) -> str:
        for attempt in range(1, retries + 1):
            try:
                resp = self.client.chat.completions.create(
                    model=self.model,
                    max_tokens=2000,
                    temperature=0,
                    messages=[
                        {"role": "system", "content": TRANSLATE_SYSTEM_PROMPT},
                        {"role": "user", "content": text},
                    ],
                )
                return resp.choices[0].message.content.strip()
            except (APIError, APIStatusError) as e:
                if attempt == retries:
                    raise
                wait = 2 ** attempt
                print(f"  [warn] API 调用失败（第{attempt}次）：{e}，{wait}s 后重试", file=sys.stderr)
                time.sleep(wait)
        raise RuntimeError("unreachable")


def needs_translation(current_value: str, i18n_entry: dict | None) -> bool:
    """判断当前字段是否需要（重新）翻译。"""
    if not current_value.strip():
        return False
    if i18n_entry is None:
        return True
    # 如果当前内容的 hash 命中已知的英文原文 hash，说明这就是我们已经处理过、
    # 但还没来得及替换的原文（理论上不会出现，防御性判断）。
    # 如果当前内容既不是已记录的英文原文，也不等于我们理应写入的中文，
    # 说明字段被人手工改过，出于安全起见也重新走一遍翻译（覆盖式，保持简单）。
    return True


def process_field(data: dict, field: str, translator: Translator, changed: list[str]) -> None:
    current = data.get(field, "")
    if not isinstance(current, str) or not current.strip():
        return

    i18n = data.setdefault("i18n", {})
    entry = i18n.get(field)

    current_hash = sha256(current)

    if entry and entry.get("zh_sha256") == current_hash:
        # 当前值就是我们上次写入的翻译结果，且英文原文没变过 -> 跳过
        return

    if entry and entry.get("en_sha256") and entry.get("en_sha256") != current_hash \
            and entry.get("zh_sha256") != current_hash:
        # 当前值既不是我们记录的英文原文也不是我们写入的中文译文
        # -> 视为上游更新了英文原文，重新翻译
        pass

    english_source = current
    # 如果当前值其实是我们之前记录的英文原文（entry.en_sha256 == current_hash），
    # 说明还没翻译过，直接用它做原文；否则也只能假定 current 就是最新原文。
    if entry and entry.get("en_sha256") == current_hash:
        english_source = entry["en"]

    translated = translator.translate(english_source)

    data[field] = translated
    i18n[field] = {
        "en": english_source,
        "en_sha256": sha256(english_source),
        "zh_sha256": sha256(translated),
    }
    changed.append(field)


def process_benchmark_json(path: Path, translator: Translator, dry_run: bool) -> bool:
    data = json.loads(path.read_text(encoding="utf-8"))
    changed: list[str] = []

    process_field(data, "description", translator, changed)
    process_field(data, "hint", translator, changed)

    if not changed:
        return False

    print(f"[translate] {path} -> 更新字段: {', '.join(changed)}")
    if not dry_run:
        path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
    return True


def process_benchmark_yaml(path: Path, translator: Translator, dry_run: bool) -> bool:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not data or "flags" not in data:
        return False

    any_changed = False
    for flag in data.get("flags", []):
        changed: list[str] = []
        process_field(flag, "description", translator, changed)
        process_field(flag, "hint", translator, changed)
        if changed:
            any_changed = True
            print(f"[translate] {path} [flag={flag.get('id')}] -> 更新字段: {', '.join(changed)}")

    if not any_changed:
        return False

    if not dry_run:
        path.write_text(
            yaml.safe_dump(data, allow_unicode=True, sort_keys=False),
            encoding="utf-8",
        )
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description="翻译 benchmark.json/yaml 中的 description/hint 字段为中文")
    parser.add_argument("--root", default=".", help="仓库根目录")
    parser.add_argument("--dry-run", action="store_true", help="只打印将要变更的内容，不写入文件、不调用 API")
    parser.add_argument("--model", default=os.environ.get("TRANSLATE_MODEL", "deepseek-chat"))
    args = parser.parse_args()

    if not args.dry_run and not os.environ.get("DEEPSEEK_API_KEY"):
        print("错误: 未设置 DEEPSEEK_API_KEY", file=sys.stderr)
        return 1

    root = Path(args.root)
    translator = Translator(model=args.model, dry_run=args.dry_run)

    any_file_changed = False
    for json_path in sorted(root.rglob("benchmark.json")):
        if process_benchmark_json(json_path, translator, args.dry_run):
            any_file_changed = True
        yaml_path = json_path.with_name("benchmark.yaml")
        if yaml_path.exists():
            if process_benchmark_yaml(yaml_path, translator, args.dry_run):
                any_file_changed = True

    if not any_file_changed:
        print("没有需要翻译/更新的字段。")

    # 写一个 flag 文件供 workflow 判断是否需要提交
    Path(".translate_changed").write_text("1" if any_file_changed else "0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
