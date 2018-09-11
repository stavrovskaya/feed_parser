from cx_Freeze import setup,Executable
import os
import sys
import numpy
import pandas
 
 
os.environ['TCL_LIBRARY'] = 'C:\\Users\\Lenovo\\Anaconda3\\tcl\\tcl8\\8.6'
os.environ['TK_LIBRARY'] = 'C:\\Users\\Lenovo\\Anaconda3\\tcl\\tk8.6'
 
path_platforms = ( "C:\\Users\\Lenovo\\Anaconda3\\pkgs\\qt-5.9.5-vc14he4a7d60_0\\Library\\plugins\\platforms\\qwindows.dll", "platforms\qwindows.dll" )
path_mkl = ( "C:\\Users\\Lenovo\\Anaconda3\\Library\\bin\\mkl_intel_thread.dll", "lib\\numpy\\mkl_intel_thread.dll" )
 
includes = ["PyQt5.QtCore","PyQt5.QtGui", "PyQt5.QtWidgets", "pandas", "numpy", "numpy.core._methods"]
includefiles = [path_platforms, path_mkl,'zvlogo.png', 'feed_parser.py']
excludes = [
    '_gtkagg', '_tkagg', 'bsddb', 'curses', 'pywin.debugger',
    'pywin.debugger.dbgcon', 'pywin.dialogs', 'tcl',
    'Tkconstants', 'Tkinter'
]

path = []
packages = ["os", "numpy.lib.format"]
 
# Dependencies are automatically detected, but it might need fine tuning.
build_exe_options = {
                     "includes":      includes,
                     "include_files": includefiles,
                     "excludes":      excludes,
                     "packages":      packages,
                     "path":          path
}
 
# GUI applications require a different base on Windows (the default is for a
# console application).
base = None
exe = None
if sys.platform == "win32":
    exe = Executable(
      script="feed_parser_gui.py",
      initScript = None,
      base="Win32GUI",
      targetName="feed_parser.exe",
      icon = None
    )
 
setup(
      name = "telll",
      version = "0.1",
      author = 'me',
      description = "My GUI application!",
      options = {"build_exe": build_exe_options},
      executables = [exe]
)