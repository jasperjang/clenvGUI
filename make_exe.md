# How I made a .exe file
## In Windows:
1. First I pip installed pyinstaller using command prompt

```
py -m pip install pyinstaller
```

2. Then I cd'd into the clenvGUI directory and ran:

```
C:/path/to/pyinstaller.exe --onefile gui.py
```

3. Once pyinstaller is finished, the .exe file should be located under the dist directory

## In Linux
1. First I pip installed pyinstaller using a terminal

```
pip install pyinstaller
```

2. Then cd into the clenvGUI directory and run:

```
pyinstaller --onefile gui.py
```

3. Once pyinstaller is finished, the .exe file should be located under the dist directory