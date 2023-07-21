from cx_Freeze import setup, Executable
import sys
print(sys.platform)
# Define your main script here (replace 'your_script.py' with the actual name of your Python script)
main_script = 'clenv_gui.py'

# Set up the options for freezing
options = {
    'build_exe': {
        'packages': ['clenv', 'clearml', 'PySimpleGUI'],  # List any additional packages your script depends on
        'include_files': ['logo.png'],  # List any additional non-Python files needed by your script
    }
}
base = None
if (sys.platform == "win32"):
    base = "Win32GUI"    # Tells the build script to hide the console.

# Create the executable
executables = [Executable(main_script, base=base)]

# Set up the setup function
setup(name='CLENV',
      version='1.0',
      description='A GUI for the clenv cli application',
      options=options,
      executables=executables)
