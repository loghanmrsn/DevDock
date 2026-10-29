# PyInstaller 6.12.0, exécuté depuis la racine du dépôt.
a = Analysis(['app.py'], pathex=[], binaries=[],
             datas=[('theme.qss', '.'), ('example', 'example')],
             hiddenimports=[], hookspath=[], hooksconfig={}, runtime_hooks=[],
             excludes=['tkinter'], noarchive=False)
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, [], exclude_binaries=True, name='DevDock',
          debug=False, bootloader_ignore_signals=False, strip=False,
          upx=False, console=False)
coll = COLLECT(exe, a.binaries, a.datas, strip=False, upx=False, name='DevDock')
