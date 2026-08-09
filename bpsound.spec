# -*- mode: python ; coding: utf-8 -*-

import os
import imageio_ffmpeg

from PyInstaller.utils.hooks import collect_all


# ============================================================
# MOVIEPY
# ============================================================

datas = []
binaries = []
hiddenimports = []

tmp_ret = collect_all("moviepy")
datas += tmp_ret[0]
binaries += tmp_ret[1]
hiddenimports += tmp_ret[2]


# ============================================================
# IMAGEIO-FFMPEG
# ============================================================

tmp_ret = collect_all("imageio_ffmpeg")
datas += tmp_ret[0]
binaries += tmp_ret[1]
hiddenimports += tmp_ret[2]


# ============================================================
# PASTIKAN FFmpeg EXE MASUK KE BUNDLE
# ============================================================

ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()

print("FFmpeg yang akan dibundle:")
print(ffmpeg_exe)

if os.path.exists(ffmpeg_exe):

    binaries.append(
        (
            ffmpeg_exe,
            "imageio_ffmpeg/binaries"
        )
    )

else:
    raise FileNotFoundError(
        f"FFmpeg tidak ditemukan: {ffmpeg_exe}"
    )


# ============================================================
# ANALYSIS
# ============================================================

a = Analysis(
    ["bpsound.py"],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)


pyz = PYZ(a.pure)


# ============================================================
# EXE
# ============================================================

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="bpsound",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)