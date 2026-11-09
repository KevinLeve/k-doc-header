# PyInstaller spec for K-Doc Header (single windowed executable).
# Build:  pyinstaller --noconfirm --clean packaging\kdoc_header.spec --distpath dist --workpath build
# Output: dist\K-Doc Header.exe
import os

ROOT = os.path.abspath(os.path.join(SPECPATH, ".."))

datas = [
    (os.path.join(ROOT, "signature_map.json"), "."),
    (os.path.join(ROOT, "assets", "kdoc_header.ico"), "assets"),
    (os.path.join(ROOT, "assets", "kdoc_header_header.png"), "assets"),
]

a = Analysis(
    [os.path.join(ROOT, "app.py")],
    pathex=[ROOT],
    datas=datas,
    hiddenimports=["engine", "tkinterdnd2"],
)

pyz = PYZ(a.pure)
VERSION_FILE = os.path.join(SPECPATH, "kdoc_header_version_info.txt")
ICON_FILE = os.path.join(ROOT, "assets", "kdoc_header.ico")
exe = EXE(
    pyz, a.scripts, a.binaries, a.datas, [],
    name="K-Doc Header", console=False, upx=False,
    version=VERSION_FILE, icon=ICON_FILE,
)
