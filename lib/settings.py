"""routewise.toml: the project's settings, checked before anything is written."""

import re
import tomllib
import unicodedata
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any

from paths import relative
from roles import MODEL, STAND_IN, TIERS, RoleError, skill_names

NAME = "routewise.toml"
HARNESSES = ("cc", "agy")
FRAGMENTS = ("dev", "assistant")
CLAUDE_MD = ("auto", "import", "none")
DEFAULT_LOG = "logs/delegation-misses.jsonl"


class SettingsError(Exception):
    """A setting that is missing, of the wrong type or out of range."""


@dataclass(frozen=True)
class Binding:
    """[binding]: the person's entries the binding is rendered from (R14); empty when unset."""

    approved_by: str = ""
    approved_on: str = ""
    approved_rules_version: int = 0  # 0: no approval recorded
    assistant_pins: str = ""
    review_from: str = ""


BINDING_TEXT = ("approved_by", "assistant_pins")
BINDING_DATES = ("approved_on", "review_from")
BINDING_KEYS = (*BINDING_TEXT, *BINDING_DATES, "approved_rules_version")
ISO_DATE = re.compile(r"\d{4}-\d{2}-\d{2}")
MAX_TEXT = 200
PLACEHOLDER_NAME = "_who, when_"  # the pre-0.4.0 template's blank: not a name
HIDDEN = ("Cc", "Cf", "Zl", "Zp")  # control, format (bidi), line and paragraph separators
BREAKING = ("|", "<", "-->", "{{")  # a table cell, HTML, the marker's end, a placeholder


@dataclass(frozen=True)
class Settings:
    harnesses: list[str] = field(default_factory=lambda: ["cc"])
    instructions: list[str] = field(default_factory=lambda: ["AGENTS.md"])
    claude_md: str = "auto"
    fragment: str = "dev"
    cap: int = 5
    miss_log: str = DEFAULT_LOG
    tiers: dict[str, str] = field(default_factory=dict)
    skills: dict[str, tuple[str, ...]] = field(default_factory=dict)  # role -> its skills (R8)
    stand_ins: dict[str, tuple[str, ...]] = field(default_factory=dict)  # role -> names (R9)
    binding: Binding = field(default_factory=Binding)


def strings(data: dict[str, Any], key: str, default: list[str]) -> list[str]:
    value = data.get(key, default)
    if not isinstance(value, list) or not all(isinstance(v, str) for v in value):
        raise SettingsError(f'{NAME}: {key} must be a list of strings, such as ["cc"]')
    return value


def text(data: dict[str, Any], key: str, default: str) -> str:
    value = data.get(key, default)
    if not isinstance(value, str):
        raise SettingsError(f"{NAME}: {key} must be a string")
    return value


def choose(key: str, values: list[str], allowed: tuple[str, ...]) -> None:
    for value in values:
        if value not in allowed:
            raise SettingsError(f"{NAME}: {key} {value!r} is not one of {', '.join(allowed)}")


def cap(data: dict[str, Any]) -> int:
    value = data.get("cap", 5)
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise SettingsError(f"{NAME}: cap must be a whole number of at least 1")
    return value


def tiers(data: dict[str, Any]) -> dict[str, str]:
    value = data.get("tiers", {})
    if not isinstance(value, dict):
        raise SettingsError(f"{NAME}: [tiers] must be a table")
    for tier, model in value.items():
        if tier not in TIERS:
            raise SettingsError(f"{NAME}: [tiers] {tier!r} is not one of {', '.join(TIERS)}")
        if not isinstance(model, str) or not MODEL.fullmatch(model):
            raise SettingsError(f"{NAME}: [tiers] {tier} must be a model name, such as haiku")
    return dict(value)


def skills(data: dict[str, Any]) -> dict[str, tuple[str, ...]]:
    """[skills]: role -> skill names, replacing the role's own list; roles are checked later."""
    value = data.get("skills", {})
    if not isinstance(value, dict):
        raise SettingsError(f"{NAME}: [skills] must be a table")
    chosen: dict[str, tuple[str, ...]] = {}
    for role, names in value.items():
        if not isinstance(names, list) or not all(isinstance(n, str) for n in names):
            example = '["plugin:skill"]'
            raise SettingsError(f"{NAME}: [skills] {role} must be a list of skill names, {example}")
        try:
            chosen[role] = skill_names(f"{NAME}: [skills] {role}", names)
        except RoleError as err:
            raise SettingsError(str(err)) from err
    return chosen


def stand_ins(data: dict[str, Any]) -> dict[str, tuple[str, ...]]:
    """[stand_ins]: role -> extra agent names; each name once, a plain file name."""
    value = data.get("stand_ins", {})
    if not isinstance(value, dict):
        raise SettingsError(f"{NAME}: [stand_ins] must be a table")
    chosen: dict[str, tuple[str, ...]] = {}
    seen: set[str] = set()
    for role, names in value.items():
        if not isinstance(names, list) or not all(isinstance(n, str) for n in names):
            example = '["code-reviewer"]'
            raise SettingsError(
                f"{NAME}: [stand_ins] {role} must be a list of agent names, {example}"
            )
        for name in names:
            if not STAND_IN.fullmatch(name):
                rule = "lower-case letters, digits and -"
                raise SettingsError(f"{NAME}: [stand_ins] stand-in name {name!r} must be {rule}")
            if name in seen:
                raise SettingsError(f"{NAME}: [stand_ins] stand-in name {name!r} is listed twice")
            seen.add(name)
        chosen[role] = tuple(names)
    return chosen


def binding_text(key: str, value: Any) -> str:
    """One line of plain text that cannot break the binding's table or end its marker."""
    where = f"{NAME}: [binding] {key}"
    if not isinstance(value, str):
        raise SettingsError(f'{where} must be text, such as "Ann (maintainer)"')
    if any(unicodedata.category(char) in HIDDEN for char in value):
        raise SettingsError(f"{where} must be one line, with no tabs or control characters")
    if any(mark in value for mark in BREAKING):
        raise SettingsError(f"{where} must not hold | < --> or {{{{, which would break the binding")
    if len(value) > MAX_TEXT:
        raise SettingsError(f"{where} must be at most {MAX_TEXT} characters")
    return value


def binding_date(key: str, value: Any) -> str:
    """A date as YYYY-MM-DD: a TOML date or a string in that form."""
    if type(value) is date:  # a TOML date; a date-time is refused
        return value.isoformat()
    if isinstance(value, str) and (value == "" or ISO_DATE.fullmatch(value)):
        try:
            return value and date.fromisoformat(value).isoformat()
        except ValueError:
            pass
    raise SettingsError(f'{NAME}: [binding] {key} must be a date, such as "2026-11-18"')


def binding(data: dict[str, Any]) -> Binding:
    """[binding]: optional; every key optional; unknown keys refused (R14)."""
    value = data.get("binding", {})
    if not isinstance(value, dict):
        raise SettingsError(f"{NAME}: [binding] must be a table")
    for key in value:
        if key not in BINDING_KEYS:
            raise SettingsError(f"{NAME}: [binding] {key} is not one of {', '.join(BINDING_KEYS)}")
    version = value.get("approved_rules_version", 0)
    if isinstance(version, bool) or not isinstance(version, int) or version < 0:
        raise SettingsError(
            f"{NAME}: [binding] approved_rules_version must be a whole number, such as 4"
        )
    if "approved_rules_version" in value and version == 0:
        raise SettingsError(
            f"{NAME}: [binding] approved_rules_version must be a whole number of at least 1"
        )
    texts = {key: binding_text(key, value.get(key, "")) for key in BINDING_TEXT}
    by = texts["approved_by"]
    if by and (not by.strip() or by.strip() == PLACEHOLDER_NAME):
        raise SettingsError(
            f'{NAME}: [binding] approved_by must name the person who approved, or be ""'
        )
    dates = {key: binding_date(key, value.get(key, "")) for key in BINDING_DATES}
    return Binding(approved_rules_version=version, **texts, **dates)


def parse(source: str) -> Settings:
    try:
        data = tomllib.loads(source)
    except tomllib.TOMLDecodeError as err:
        raise SettingsError(f"{NAME}: {err}") from err
    settings = Settings(
        harnesses=strings(data, "harnesses", ["cc"]),
        instructions=strings(data, "instructions", ["AGENTS.md"]),
        claude_md=text(data, "claude_md", "auto"),
        fragment=text(data, "fragment", "dev"),
        cap=cap(data),
        miss_log=text(data, "miss_log", DEFAULT_LOG),
        tiers=tiers(data),
        skills=skills(data),
        stand_ins=stand_ins(data),
        binding=binding(data),
    )
    choose("harness", settings.harnesses, HARNESSES)
    choose("fragment", [settings.fragment], FRAGMENTS)
    choose("claude_md", [settings.claude_md], CLAUDE_MD)
    for name in [*settings.instructions, settings.miss_log]:
        relative(name, "path")
    return settings


def read(root: Path) -> Settings | None:
    path = root / NAME
    return parse(path.read_text(encoding="utf-8")) if path.exists() else None
