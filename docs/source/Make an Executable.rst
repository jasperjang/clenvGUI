How to make an executable file
=============================
In Windows
----------
1. CD into the clenvGUI directory::
    
    cd path\to\clenvGUI

2. Create a virtual environment and activate it::

    py -m venv clenv_env
    .\clenv_env\Scripts\activate.ps1

2. Pip install requirements.txt::

    py -m pip install -r requirements.txt

3. Open the the following file in VScode::

    code .\clenv_env\Lib\site-packages\orderedmultidict\__init__.py

4. Replace the contents of __init__.py with the following code and save::

    # -*- coding: utf-8 -*-
    #
    # omdict - Ordered Multivalue Dictionary.
    #
    # Ansgar Grunseid
    # grunseid.com
    # grunseid@gmail.com
    #
    # License: Build Amazing Things (Unlicense)
    #

    from os.path import dirname, join as pjoin
    from .orderedmultidict import *  # noqa

    # Import all variables in __version__.py without explicit imports.
    from . import __version__
    globals().update(dict(
        (k, v) for k, v in __version__.__dict__.items()
        if k not in globals()))

5. Create the executable by running the following code in the terminal::

    py setup.py build

6. The executable should be found in the directory within the build directory as clenv_gui.exe

In Linux
--------
1. CD into the clenvGUI directory::

    cd path/to/clenvGUI

2. Create a virtual environment and activate it::

    python3 -m venv clenv_env
    ./clenv_env/bin/activate

2. Pip install requirements.txt::

    pip install -r requirements.txt

3. Open the the following file in VScode::

    code ./clenv_env/lib/python3.10/site-packages/orderedmultidict/__init__.py

4. Replace the contents of __init__.py with the following code and save::

    # -*- coding: utf-8 -*-
    #
    # omdict - Ordered Multivalue Dictionary.
    #
    # Ansgar Grunseid
    # grunseid.com
    # grunseid@gmail.com
    #
    # License: Build Amazing Things (Unlicense)
    #

    from os.path import dirname, join as pjoin
    from .orderedmultidict import *  # noqa

    # Import all variables in __version__.py without explicit imports.
    from . import __version__
    globals().update(dict(
        (k, v) for k, v in __version__.__dict__.items()
        if k not in globals()))

5. Create the executable by running the following code in the terminal::

    python3 setup.py build

6. The executable should be found in the directory within the build directory as clenv_gui
