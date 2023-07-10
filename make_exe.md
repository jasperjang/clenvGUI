# How I made a .exe file
## In Windows
1. First pip install pyinstaller using command prompt

```
py -m pip install pyinstaller
```

2. Then cd into the clenvGUI directory and run the following command in the terminal:

```
C:/path/to/pyinstaller.exe --onefile gui.py
```

3. Once pyinstaller is finished, the .exe file should be located under the dist directory

## In Linux
1. First pip install pyinstaller using a terminal

```
pip install pyinstaller
```

2. Then cd into the clenvGUI directory and run the following command in the terminal:

```
pyinstaller --onefile gui.py
```

3. Once pyinstaller is finished, the .exe file should be located under the dist directory