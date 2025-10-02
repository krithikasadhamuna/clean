
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('config.yaml', '.'),
        ('README.md', '.'),
        ('requirements.txt', '.'),
        ('core', 'core'),
        ('shared', 'shared')
    ],
    hiddenimports=[
        'win32evtlog',
        'win32evtlogutil', 
        'win32con',
        'win32service',
        'win32net',
        'winreg',
        'psutil',
        'requests',
        'docker',
        'aiohttp',
        'asyncio',
        'yaml',
        'json',
        'logging',
        'pathlib',
        'subprocess',
        'platform',
        'uuid',
        'datetime',
        'typing',
        'ctypes',
        'wmi',
        'network_discovery',
        'location_detector',
        'container_orchestrator',
        'config_manager',
        'core.client.client_agent',
        'core.client.command_executor',
        'core.client.container_attack_executor',
        'core.client.container_manager',
        'core.client.forwarders.windows_forwarder',
        'core.client.forwarders.linux_forwarder',
        'core.client.forwarders.application_forwarder',
        'core.client.forwarders.ebpf_forwarder',
        'core.client.forwarders.base_forwarder',
        'shared.config',
        'shared.models',
        'shared.utils'
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter',
        'matplotlib',
        'numpy',
        'pandas',
        'scipy',
        'PIL',
        'cv2'
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
    name='CodeGrey-Agent-Windows',
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
    icon='codegrey-icon.ico' if os.path.exists('codegrey-icon.ico') else None,
    version_file='version_info.txt' if os.path.exists('version_info.txt') else None
)
