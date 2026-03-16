#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Publish skills from local Hub to remote store.

This script publishes skills from the local enterprise Hub to a remote
skills store (e.g., Convex-based backend).
"""
import json
import os
import sys
import zipfile
import io
from pathlib import Path
from typing import Any
from urllib.error import HTTPError
from urllib.request import Request, urlopen


def fetch_skill_from_local_hub(hub_url: str, slug: str) -> dict[str, Any]:
    """Fetch skill bundle from local Hub.

    Args:
        hub_url: Local Hub URL (e.g., http://127.0.0.1:9090)
        slug: Skill slug

    Returns:
        Skill bundle dict
    """
    url = f"{hub_url.rstrip('/')}/api/v1/skills/{slug}"

    req = Request(
        url,
        headers={
            "Accept": "application/json",
        },
    )

    with urlopen(req, timeout=30) as resp:
        body = resp.read().decode("utf-8")
        return json.loads(body)


def create_skill_zip(bundle: dict[str, Any]) -> bytes:
    """Create a ZIP file from skill bundle.

    Args:
        bundle: Skill bundle from Hub

    Returns:
        ZIP file as bytes
    """
    buffer = io.BytesIO()

    with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
        # Add SKILL.md
        content = bundle.get('content', '')
        zf.writestr('SKILL.md', content)

        # Add files
        files = bundle.get('files', {})
        for path, file_content in files.items():
            if path != 'SKILL.md':  # Don't duplicate
                zf.writestr(path, file_content)

    buffer.seek(0)
    return buffer.read()


def publish_to_remote_store(
    remote_url: str,
    slug: str,
    bundle: dict[str, Any],
    zip_data: bytes,
    dry_run: bool = False,
    api_key: str | None = None,
) -> dict[str, Any]:
    """Publish skill to remote store.

    Args:
        remote_url: Remote store base URL
        slug: Skill slug
        bundle: Skill bundle dict
        zip_data: ZIP file bytes
        dry_run: If True, don't actually upload
        api_key: Optional API key for authentication

    Returns:
        Response dict
    """
    # Extract metadata from bundle
    skill = bundle.get('skill', {})
    version = bundle.get('version', {})
    name = skill.get('name', slug)
    display_name = skill.get('displayName', name)
    description = skill.get('description', '')
    version_str = skill.get('version', '1.0.0')

    # Prepare multipart/form-data payload
    boundary = '----WebKitFormBoundary' + ''.join([str(i) for i in range(16)])

    body_parts = []

    # Add metadata fields
    fields = {
        'slug': slug,
        'name': name,
        'displayName': display_name,
        'description': description,
        'version': version_str,
        'changelog': f'Published from local Hub: {name}',
    }

    for field_name, field_value in fields.items():
        body_parts.append(
            f'--{boundary}\r\n'
            f'Content-Disposition: form-data; name="{field_name}"\r\n'
            f'\r\n'
            f'{field_value}\r\n'
        )

    # Add ZIP file
    body_parts.append(
        f'--{boundary}\r\n'
        f'Content-Disposition: form-data; name="file"; filename="{slug}-{version_str}.zip"\r\n'
        f'Content-Type: application/zip\r\n'
        f'\r\n'
    )
    body = ''.join(body_parts).encode('utf-8')
    body += zip_data
    body += f'\r\n--{boundary}--\r\n'.encode('utf-8')

    if dry_run:
        return {
            'success': True,
            'message': 'DRY RUN - Would upload skill',
            'slug': slug,
            'size': len(body),
            'fields': fields,
        }

    # Try different upload endpoints
    upload_endpoints = [
        f'{remote_url.rstrip("/")}/api/v1/skills',
        f'{remote_url.rstrip("/")}/api/v1/skills/{slug}',
        f'{remote_url.rstrip("/")}/api/v1/upload',
    ]

    last_error = None
    for upload_url in upload_endpoints:
        try:
            headers = {
                'Content-Type': f'multipart/form-data; boundary={boundary}',
                'Accept': 'application/json',
            }
            if api_key:
                headers['Authorization'] = f'Bearer {api_key}'

            req = Request(
                upload_url,
                data=body,
                headers=headers,
            )

            with urlopen(req, timeout=60) as resp:
                response_body = resp.read().decode('utf-8')
                if response_body:
                    return json.loads(response_body)
                return {'success': True, 'url': upload_url}

        except HTTPError as e:
            last_error = e
            code = getattr(e, 'code', 0)
            if code == 404:
                continue  # Try next endpoint
            if code == 405:
                continue  # Method not allowed, try next endpoint
            raise
        except Exception as e:
            last_error = e
            continue

    # If we get here, all endpoints failed
    if last_error:
        raise RuntimeError(f'Failed to upload to any endpoint. Last error: {last_error}')
    raise RuntimeError('Failed to upload: No valid upload endpoint found')


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description='Publish skills from local Hub to remote store'
    )
    parser.add_argument(
        '--slug',
        default='weather-query',
        help='Skill slug to publish (default: weather-query)',
    )
    parser.add_argument(
        '--remote',
        default='https://wry-manatee-359.convex.site',
        help='Remote store URL',
    )
    parser.add_argument(
        '--hub',
        default='http://127.0.0.1:9090',
        help='Local Hub URL',
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Preview mode - show what would be done',
    )
    parser.add_argument(
        '--api-key',
        help='API key for remote store authentication',
    )

    args = parser.parse_args()

    # Get API key from env var if not provided
    api_key = args.api_key or os.environ.get('REMOTE_STORE_API_KEY')

    print(f'Publishing skill: {args.slug}')
    print(f'From local Hub: {args.hub}')
    print(f'To remote store: {args.remote}')
    if api_key:
        print(f'Using API key: {api_key[:10]}...' if len(api_key) > 10 else 'Using API key: ***')
    else:
        print('Warning: No API key provided - upload may fail')
    print()

    # Fetch from local Hub
    print(f'Fetching skill from local Hub...')
    bundle = fetch_skill_from_local_hub(args.hub, args.slug)
    print(f'  ✓ Fetched: {bundle["skill"]["name"]} v{bundle["skill"]["version"]}')

    # Create ZIP
    print(f'Creating ZIP file...')
    zip_data = create_skill_zip(bundle)
    print(f'  ✓ ZIP size: {len(zip_data)} bytes')

    # Publish to remote
    print(f'Publishing to remote store...')
    if args.dry_run:
        print('  DRY RUN MODE - skipping upload')
        result = publish_to_remote_store(
            args.remote, args.slug, bundle, zip_data, dry_run=True, api_key=api_key
        )
        print(f'  Would upload {result["size"]} bytes with fields:')
        for k, v in result['fields'].items():
            print(f'    {k}: {v}')
    else:
        result = publish_to_remote_store(
            args.remote, args.slug, bundle, zip_data, dry_run=False, api_key=api_key
        )
        print(f'  ✓ Published successfully!')
        print(f'  Result: {json.dumps(result, indent=2)[:500]}...')


if __name__ == '__main__':
    main()
