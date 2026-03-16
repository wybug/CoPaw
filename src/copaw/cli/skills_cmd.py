# -*- coding: utf-8 -*-
"""CLI skill: list and interactively enable/disable skills."""
from __future__ import annotations

import click

from ..agents.skills_manager import SkillService, list_available_skills
from ..agents.skills_hub import (
    HubInstallResult,
    _get_employee_id,
    _get_enterprise_allowed_sources,
    _hub_base_url,
    _hub_detail_path,
    _is_enterprise_mode,
    _join_url,
    install_skill_from_hub,
    search_hub_skills,
)
from .utils import prompt_checkbox, prompt_confirm


# pylint: disable=too-many-branches
def configure_skills_interactive() -> None:
    """Interactively select which skills to enable (multi-select)."""
    all_skills = SkillService.list_all_skills()
    if not all_skills:
        click.echo("No skills found. Nothing to configure.")
        return

    available = set(list_available_skills())
    all_names = {s.name for s in all_skills}

    # Default to all skills if nothing is currently active (first time)
    default_checked = available if available else all_names

    # Build checkbox options: (label, value)
    options: list[tuple[str, str]] = []
    for skill in sorted(all_skills, key=lambda s: s.name):
        status = "✓" if skill.name in available else "✗"
        label = f"{skill.name}  [{status}] ({skill.source})"
        options.append((label, skill.name))

    click.echo("\n=== Skills Configuration ===")
    click.echo("Use ↑/↓ to move, <space> to toggle, <enter> to confirm.\n")

    selected = prompt_checkbox(
        "Select skills to enable:",
        options=options,
        checked=default_checked,
        select_all_option=False,
    )

    # Ctrl+C → cancel
    if selected is None:
        click.echo("\n\nOperation cancelled.")
        return

    selected_set = set(selected)

    # Show preview of changes
    to_enable = selected_set - available
    to_disable = (all_names & available) - selected_set

    if not to_enable and not to_disable:
        click.echo("\nNo changes needed.")
        return

    click.echo()
    if to_enable:
        click.echo(
            click.style(
                f"  + Enable:  {', '.join(sorted(to_enable))}",
                fg="green",
            ),
        )
    if to_disable:
        click.echo(
            click.style(
                f"  - Disable: {', '.join(sorted(to_disable))}",
                fg="red",
            ),
        )

    # Confirm save or skip
    save = prompt_confirm("Apply changes?", default=True)
    if not save:
        click.echo("Skipped. No changes applied.")
        return

    # Apply changes
    for name in to_enable:
        result = SkillService.enable_skill(name)
        if result:
            click.echo(f"  ✓ Enabled: {name}")
        else:
            click.echo(
                click.style(f"  ✗ Failed to enable: {name}", fg="red"),
            )

    for name in to_disable:
        result = SkillService.disable_skill(name)
        if result:
            click.echo(f"  ✓ Disabled: {name}")
        else:
            click.echo(
                click.style(f"  ✗ Failed to disable: {name}", fg="red"),
            )

    click.echo("\n✓ Skills configuration updated!")


@click.group("skills")
def skills_group() -> None:
    """Manage skills (list / configure)."""


@skills_group.command("list")
def list_cmd() -> None:
    """Show all skills and their enabled/disabled status."""
    all_skills = SkillService.list_all_skills()
    available = set(list_available_skills())

    if not all_skills:
        click.echo("No skills found.")
        return

    click.echo(f"\n{'─' * 50}")
    click.echo(f"  {'Skill Name':<30s} {'Source':<12s} Status")
    click.echo(f"{'─' * 50}")

    for skill in sorted(all_skills, key=lambda s: s.name):
        status = (
            click.style("✓ enabled", fg="green")
            if skill.name in available
            else click.style("✗ disabled", fg="red")
        )
        click.echo(f"  {skill.name:<30s} {skill.source:<12s} {status}")

    click.echo(f"{'─' * 50}")
    enabled_count = sum(1 for s in all_skills if s.name in available)
    click.echo(
        f"  Total: {len(all_skills)} skills, "
        f"{enabled_count} enabled, "
        f"{len(all_skills) - enabled_count} disabled\n",
    )


@skills_group.command("config")
def configure_cmd() -> None:
    configure_skills_interactive()


@skills_group.command("search")
@click.argument("query", default="")
@click.option("--limit", default=20, help="最大结果数")
def search_cmd(query: str, limit: int) -> None:
    """从技能中心搜索技能。"""
    try:
        results = search_hub_skills(query, limit)

        click.echo(f"\n{'=' * 50}")
        click.echo(f"  找到 {len(results)} 个技能")
        click.echo(f"{'=' * 50}\n")

        if not results:
            click.echo("未找到匹配的技能。")
            if _is_enterprise_mode():
                click.echo("\n企业模式已启用，仅显示企业技能中心的技能。")
            return

        for skill in results:
            click.echo(f"名称: {skill.name}")
            click.echo(f"标识: {skill.slug}")
            desc = skill.description[:80] + "..." if len(skill.description) > 80 else skill.description
            click.echo(f"描述: {desc}")
            if skill.version:
                click.echo(f"版本: {skill.version}")
            click.echo("---")

        # Show install hint
        click.echo(f"\n提示: 使用 'copaw skills install <标识>' 安装技能")

    except Exception as e:
        click.echo(f"搜索失败: {e}", err=True)
        raise click.ClickException(str(e))


@skills_group.command("install")
@click.argument("slug")
@click.option("--version", default="", help="指定版本")
@click.option("--no-enable", is_flag=True, help="安装后不启用")
@click.option("--force", is_flag=True, help="覆盖已存在的技能")
def install_cmd(slug: str, version: str, no_enable: bool, force: bool) -> None:
    """从技能中心安装技能（支持通过 slug 安装）。"""
    from ..agents.skills_hub import _enforce_enterprise_mode

    # Enforce enterprise mode restrictions
    _enforce_enterprise_mode()

    # Build bundle URL
    if _is_enterprise_mode():
        base_url = _hub_base_url()
        detail_path = _hub_detail_path().format(slug=slug)
        bundle_url = _join_url(base_url, detail_path)
        click.echo(f"企业模式：从 {bundle_url} 安装")
        click.echo(f"员工 ID: {_get_employee_id()}")
        click.echo("将进行签名验证...")
    else:
        # Standard mode: use clawhub.ai
        bundle_url = f"https://clawhub.ai/skills/{slug}"
        click.echo(f"从 {bundle_url} 安装")

    try:
        result = install_skill_from_hub(
            bundle_url=bundle_url,
            version=version,
            enable=not no_enable,
            overwrite=force,
        )

        click.echo(f"\n{'=' * 50}")
        click.echo("  安装成功")
        click.echo(f"{'=' * 50}")
        click.echo(f"名称: {result.name}")
        click.echo(f"状态: {'已启用' if result.enabled else '已安装但未启用'}")
        click.echo(f"来源: {result.source_url}")

    except Exception as e:
        click.echo(f"\n{'=' * 50}", err=True)
        click.echo("  安装失败", err=True)
        click.echo(f"{'=' * 50}", err=True)
        click.echo(f"错误: {e}", err=True)
        raise click.ClickException(str(e))


@skills_group.command("security")
def security_cmd() -> None:
    """显示当前安全配置。"""
    click.echo("=== 技能安全配置 ===\n")

    is_enterprise = _is_enterprise_mode()
    mode_str = "企业" if is_enterprise else "标准"
    click.echo(f"模式: {mode_str}")

    if is_enterprise:
        click.echo(f"Hub URL: {_hub_base_url()}")
        sources = _get_enterprise_allowed_sources()
        click.echo(f"允许的来源: {', '.join(sources)}")
        click.echo(f"\n配置：通过 COPAW_SKILLS_ALLOWED_SOURCES 环境变量")
    else:
        click.echo("标准模式：无限制")
