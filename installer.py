import PyInstaller.__main__

PyInstaller.__main__.run([
    '--add-data=web:web',
    '--add-data=images:images',
    'main.py',
    '--name=rggbar',
    '--onefile',
    '--paths=.\\venv\\Lib\\site-packages',
    '--noconfirm',
    '--icon=images/rggbar_logo.ico'
])
