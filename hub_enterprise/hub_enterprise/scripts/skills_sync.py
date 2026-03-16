#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Skills sync CLI for enterprise CoPaw.

This script provides command-line tools for syncing skills from various
sources (GitHub, skills.sh, skillsmp.com) to an enterprise Hub with
automatic signing and approval capabilities.

Usage:
    skills-sync sync <source> <identifier> [OPTIONS]
    skills-sync generate-key-pair [--output DIR]
"""
import sys
import os
from pathlib import Path

# Add parent directory to path for imports
_script_dir = Path(__file__).parent
if str(_script_dir) not in sys.path:
    sys.path.insert(0, str(_script_dir))

if str(_script_dir.parent) not in sys.path:
    sys.path.insert(0, str(_script_dir.parent))

import click
import frontmatter

from .config import load_config
from .logger import get_logger, SyncResult
from .fetchers import get_fetcher, detect_source, FetchResult
from .signer import create_signer, generate_and_save_key_pair, print_key_info
from .submitter import HubSubmitter, DirectHubApprover


@click.group()
@click.version_option(version="1.0.0")
def cli() -> None:
    """Skills sync CLI for enterprise CoPaw.

    Sync skills from GitHub, skills.sh, and skillsmp.com to your
    enterprise Hub with automatic RSA signing and approval.
    """
    pass


@cli.command(name="sync")
@click.argument("source", required=False)
@click.argument("identifier", required=False)
@click.option(
    "--hub-url",
    envvar="HUB_SYNC_URL",
    default="http://localhost:9090",
    help="Hub server URL (default: http://localhost:9090)",
)
@click.option(
    "--private-key",
    envvar="HUB_SYNC_PRIVATE_KEY",
    help="RSA private key in PEM format for signing",
)
@click.option(
    "--private-key-file",
    envvar="HUB_SYNC_PRIVATE_KEY_FILE",
    type=click.Path(exists=True, path_type=Path),
    help="Path to file containing RSA private key",
)
@click.option(
    "--auto-approve/--no-auto-approve",
    default=False,
    help="Automatically approve skills after submission",
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Preview mode: show what would be done without executing",
)
@click.option(
    "--log-file",
    type=click.Path(path_type=Path),
    help="Path to log file for detailed output",
)
@click.option(
    "--verbose", "-v",
    is_flag=True,
    help="Enable verbose/debug logging",
)
@click.option(
    "--quiet", "-q",
    is_flag=True,
    help="Suppress console output",
)
@click.option(
    "--direct",
    is_flag=True,
    help="Use direct storage mode (requires HUB_DATA_DIR)",
)
@click.option(
    "--data-dir",
    envvar="HUB_DATA_DIR",
    type=click.Path(exists=True, path_type=Path),
    help="Hub data directory for direct mode",
)
def sync_command(
    source: str | None,
    identifier: str | None,
    hub_url: str,
    private_key: str | None,
    private_key_file: Path | None,
    auto_approve: bool,
    dry_run: bool,
    log_file: Path | None,
    verbose: bool,
    quiet: bool,
    direct: bool,
    data_dir: Path | None,
) -> None:
    """Sync a skill from a source to the enterprise Hub.

    \b
    SOURCES:
        github    GitHub repository (URL or owner/repo)
        skills-sh skills.sh URL
        skills-mp skillsmp.com URL
        auto      Auto-detect from identifier

    \b
    EXAMPLES:
        # Sync from GitHub URL
        skills-sync sync github https://github.com/owner/repo

        # Sync from skills.sh
        skills-sync sync skills-sh https://skills.sh/owner/repo/skill

        # Sync with auto-approval
        skills-sync sync github owner/repo --auto-approve --private-key-file key.pem

        # Preview mode
        skills-sync sync github owner/repo --dry-run

        # Direct storage mode (bypasses HTTP API)
        skills-sync sync github owner/repo --direct --data-dir /path/to/hub/data
    """
    # Validate arguments
    if not identifier:
        raise click.UsageError("IDENTIFIER is required")

    # Convert private_key_file to string if provided
    private_key_file_str = str(private_key_file) if private_key_file else None

    # Load configuration
    try:
        config = load_config(
            hub_url=hub_url,
            private_key=private_key,
            private_key_file=private_key_file_str,
            auto_approve=auto_approve,
            dry_run=dry_run,
            log_file=str(log_file) if log_file else None,
        )
    except ValueError as e:
        raise click.ClickException(f"Configuration error: {e}")

    # Auto-detect source if not specified
    if source is None or source == "auto":
        detected_source = detect_source(identifier)
        if not quiet:
            click.echo(f"Auto-detected source: {detected_source}")
        source = detected_source

    # Get logger
    logger = get_logger(
        log_file=str(log_file) if log_file else None,
        quiet=quiet,
        verbose=verbose,
    )

    # Log operation start
    logger.info(f"Starting sync: {source} -> {config.hub_url}")
    if config.dry_run:
        logger.info("DRY RUN MODE - No changes will be made")

    try:
        result = _sync_single_skill(
            source=source,
            identifier=identifier,
            config=config,
            logger=logger,
            direct=direct,
            data_dir=str(data_dir) if data_dir else None,
        )
        logger.result(result)

        # Print summary
        logger.print_summary()

        # Exit with appropriate code
        sys.exit(0 if result.success else 1)

    except Exception as e:
        logger.error(f"Sync failed: {e}")
        if verbose:
            import traceback
            logger.error(traceback.format_exc())
        sys.exit(1)


def _sync_single_skill(
    source: str,
    identifier: str,
    config,
    logger,
    direct: bool = False,
    data_dir: str | None = None,
) -> SyncResult:
    """Sync a single skill from source to Hub.

    Args:
        source: Source type (github, skills-sh, etc.).
        identifier: Source identifier (URL, slug, etc.).
        config: SyncConfig instance.
        logger: SyncLogger instance.
        direct: Use direct storage mode.
        data_dir: Hub data directory for direct mode.

    Returns:
        SyncResult with operation outcome.
    """
    try:
        # Step 1: Fetch skill bundle
        logger.info(f"Fetching skill from {source}: {identifier}")
        fetcher = get_fetcher(source)

        if config.dry_run:
            logger.info("[DRY RUN] Would fetch from: " + identifier)
            # For dry run, we'd need to fetch anyway to show details
            # but we'll handle that as a special case

        fetch_result: FetchResult = fetcher.fetch(identifier)
        logger.info(f"Fetched skill: {fetch_result.name}")

        # Extract description from frontmatter
        description = ""
        try:
            post = frontmatter.loads(fetch_result.content)
            description = post.get("description", "")
            if not description:
                # Use first line of content as description
                lines = fetch_result.content.split("\n")
                for line in lines:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        description = line[:200]
                        break
        except Exception:
            description = f"Skill synced from {fetch_result.source_url}"

        # Generate slug if not present
        slug = fetch_result.slug or fetch_result.name.lower().replace(" ", "-")

        if config.dry_run:
            logger.info(f"[DRY RUN] Skill details:")
            logger.info(f"  Name: {fetch_result.name}")
            logger.info(f"  Slug: {slug}")
            logger.info(f"  Description: {description[:100]}...")
            logger.info(f"  Files: {len(fetch_result.files)}")
            logger.info(f"  Source: {fetch_result.source_url}")
            if config.auto_approve:
                logger.info("  [Would auto-approve with signature]")
            return SyncResult(
                success=True,
                skill_name=fetch_result.name,
                source=identifier,
                message="DRY RUN - Would submit skill",
            )

        # Step 2: Generate signature if auto-approve is enabled
        signature = ""
        if config.auto_approve:
            if not config.private_key:
                return SyncResult(
                    success=False,
                    skill_name=fetch_result.name,
                    source=identifier,
                    message="Auto-approve requires private key",
                    error="Private key not configured",
                )

            logger.info("Generating signature...")
            try:
                signer = create_signer(private_key=config.private_key)
                bundle_dict = fetch_result.to_dict()
                signature = signer.sign_bundle(bundle_dict)
                logger.info("Signature generated successfully")
            except Exception as e:
                return SyncResult(
                    success=False,
                    skill_name=fetch_result.name,
                    source=identifier,
                    message="Failed to generate signature",
                    error=str(e),
                )

        # Step 3: Submit to Hub
        if direct:
            # Direct storage mode
            logger.info(f"Submitting directly to Hub storage: {data_dir}")
            try:
                approver = DirectHubApprover(data_dir=data_dir)
                approver.approve_skill_direct(
                    slug=slug,
                    name=fetch_result.name,
                    description=description,
                    content=fetch_result.content,
                    files=fetch_result.files,
                    version=fetch_result.version,
                    signature=signature,
                    approver="skills-sync",
                )

                return SyncResult(
                    success=True,
                    skill_name=fetch_result.name,
                    source=identifier,
                    message="Skill approved directly",
                    signature=signature if signature else None,
                )
            except Exception as e:
                return SyncResult(
                    success=False,
                    skill_name=fetch_result.name,
                    source=identifier,
                    message="Direct approval failed",
                    error=str(e),
                )

        else:
            # HTTP API mode
            logger.info(f"Submitting to Hub: {config.hub_url}")
            submitter = HubSubmitter(
                hub_url=config.hub_url,
                timeout=config.timeout,
                retries=config.retries,
            )

            try:
                if signature:
                    # Try direct approval with signature
                    submit_result = submitter.submit_with_signature(
                        slug=slug,
                        name=fetch_result.name,
                        description=description,
                        content=fetch_result.content,
                        files=fetch_result.files,
                        version=fetch_result.version,
                        signature=signature,
                    )
                else:
                    # Standard submission workflow
                    submit_result = submitter.submit_skill(
                        slug=slug,
                        name=fetch_result.name,
                        description=description,
                        content=fetch_result.content,
                        files=fetch_result.files,
                        version=fetch_result.version,
                    )

                approval_id = submit_result.get("approval_id", "")

                # Auto-approve if enabled and signature wasn't used
                if config.auto_approve and not signature:
                    if approval_id:
                        logger.info(f"Auto-approving: {approval_id}")
                        submitter.approve_skill(
                            approval_id=approval_id,
                            reviewer="skills-sync",
                        )

                return SyncResult(
                    success=True,
                    skill_name=fetch_result.name,
                    source=identifier,
                    message="Skill submitted successfully",
                    approval_id=approval_id or None,
                    signature=signature or None,
                )

            except Exception as e:
                return SyncResult(
                    success=False,
                    skill_name=fetch_result.name,
                    source=identifier,
                    message="Submission failed",
                    error=str(e),
                )

    except Exception as e:
        return SyncResult(
            success=False,
            skill_name="unknown",
            source=identifier,
            message="Sync failed",
            error=str(e),
        )


@cli.command(name="generate-key-pair")
@click.option(
    "--output",
    "-o",
    type=click.Path(path_type=Path),
    default=None,
    help="Output directory for keys (default: current directory)",
)
@click.option(
    "--private-name",
    default="private_key.pem",
    help="Private key filename",
)
@click.option(
    "--public-name",
    default="public_key.pem",
    help="Public key filename",
)
def generate_key_pair_command(
    output: Path | None,
    private_name: str,
    public_name: str,
) -> None:
    """Generate a new RSA key pair for skill signing.

    Generates a 2048-bit RSA key pair for signing skills. The private
    key should be kept secure and never shared or committed to version
    control. The public key can be distributed for verification.

    \b
    The generated keys will be:
    - Private key: For signing with HUB_SYNC_PRIVATE_KEY_FILE
    - Public key: For verification with COPAW_SKILLS_HUB_PUBLIC_KEY

    \b
    EXAMPLES:
        # Generate in current directory
        skills-sync generate-key-pair

        # Generate in specific directory
        skills-sync generate-key-pair --output ~/.copaw/keys

        # Custom filenames
        skills-sync generate-key-pair --private-name hub.key --public-name hub.pub
    """
    output_dir = output if output else Path.cwd()

    try:
        private_path, public_path = generate_and_save_key_pair(
            output_dir=output_dir,
            private_key_name=private_name,
            public_key_name=public_name,
        )

        print_key_info(private_path, public_path)

    except Exception as e:
        raise click.ClickException(f"Failed to generate key pair: {e}")


@cli.command(name="verify")
@click.argument("bundle-file", type=click.Path(exists=True, path_type=Path))
@click.option(
    "--public-key",
    envvar="COPAW_SKILLS_HUB_PUBLIC_KEY",
    help="Public key in PEM format for verification",
)
@click.option(
    "--public-key-file",
    type=click.Path(exists=True, path_type=Path),
    help="Path to file containing public key",
)
@click.option(
    "--signature",
    help="Base64-encoded signature to verify",
)
def verify_command(
    bundle_file: Path,
    public_key: str | None,
    public_key_file: Path | None,
    signature: str | None,
) -> None:
    """Verify a skill bundle signature.

    Verify that a skill bundle JSON file has a valid signature.

    \b
    EXAMPLES:
        # Verify with signature in environment
        skills-sync verify bundle.json --signature "abc123..."

        # Verify with public key file
        skills-sync verify bundle.json --public-key-file public_key.pem
    """
    import json
    import sys
    import hashlib

    # Load public key
    key_content = public_key
    if not key_content and public_key_file:
        key_content = public_key_file.read_text(encoding="utf-8")

    if not key_content:
        raise click.UsageError(
            "Public key required via --public-key or --public-key-file"
        )

    # Load bundle
    try:
        with open(bundle_file, "r", encoding="utf-8") as f:
            bundle = json.load(f)
    except Exception as e:
        raise click.ClickException(f"Failed to load bundle: {e}")

    # Get signature
    sig_to_verify = signature
    if not sig_to_verify and "signature" in bundle:
        sig_to_verify = bundle["signature"]

    if not sig_to_verify:
        raise click.UsageError(
            "Signature required via --signature or in bundle file"
        )

    # Verify using hub_enterprise.signature
    try:
        from hub_enterprise.signature import SignatureVerifier

        verifier = SignatureVerifier(key_content)
        is_valid = verifier.verify_skill_bundle(bundle, sig_to_verify)

        if is_valid:
            click.echo(click.style("✓ Signature is VALID", fg="green"))
            sys.exit(0)
        else:
            click.echo(click.style("✗ Signature is INVALID", fg="red"))
            sys.exit(1)

    except ImportError:
        # Fallback verification if cryptography not available
        click.echo("Warning: cryptography library not available for full verification")
        # At least check hash
        normalized = json.dumps(bundle, sort_keys=True, ensure_ascii=False)
        bundle_hash = hashlib.sha256(normalized.encode()).hexdigest()
        click.echo(f"Bundle SHA-256: {bundle_hash}")
        sys.exit(2)


def main() -> None:
    """Main entry point for the CLI."""
    cli()


if __name__ == "__main__":
    main()
