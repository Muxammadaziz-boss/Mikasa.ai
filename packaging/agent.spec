# -*- mode: python ; coding: utf-8 -*-
# ========== packaging/agent.spec ==========
# Phase 45 — PyInstaller Specification for Mikasa Windows PC Agent
# ZERO SECRETS BUNDLED: No API keys, credentials, or private keys included in binary.

import os
import sys

block_cipher = None

# Base directory
BASE_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))

a = Analysis(
    [os.path.join(BASE_DIR, 'agent', 'windows_agent.py')],
    pathex=[BASE_DIR],
    binaries=[],
    datas=[],
    hiddenimports=[
        'agent',
        'agent.config',
        'agent.identity',
        'agent.crypto',
        'agent.audit',
        'agent.recovery',
        'agent.transport',
        'agent.enrollment',
        'agent.auth',
        'agent.heartbeat',
        'agent.startup',
        'agent.lifecycle',
        'agent.windows_agent',
        'core.v8.events',
        'core.v8.device',
        'core.v8.device_auth',
        'core.v8.heartbeat',
        'aiohttp',
        'cryptography',
        'psutil',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter',
        'unittest',
        'pytest',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='MikasaAgent',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
