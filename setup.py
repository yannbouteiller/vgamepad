from setuptools import setup, find_packages
import platform
from pathlib import Path
import subprocess
import sys

assert platform.system() == 'Windows', "Sorry, this module is only compatible with Windows so far."

if platform.architecture()[0] == "64bit":
    arch = "x64"
else:
    arch = "x86"
pathMsi = Path(__file__).parent.absolute() / "vgamepad" / "win" / "vigem" / "install" / arch / ("ViGEmBusSetup_" + arch + ".msi")

# Prompt installation of the ViGEmBus driver (blocking call)
if sys.argv[1] != 'egg_info' and sys.argv[1] != 'sdist':
    subprocess.call('msiexec /i %s' % str(pathMsi), shell=True)

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name='vgamepad',
    packages=[package for package in find_packages()],
    version='0.0.3',
    license='MIT',
    description='Virtual XBox360 and DualShock4 gamepads in python',
    long_description=long_description,
    long_description_content_type="text/markdown",
    author='Yann Bouteiller',
    url='https://github.com/yannbouteiller/vgamepad',
    download_url='https://github.com/yannbouteiller/vgamepad/archive/v0.0.3.tar.gz',
    keywords=['virtual', 'gamepad', 'python', 'xbox', 'dualshock', 'controller', 'emulator'],
    install_requires=[],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Intended Audience :: Education',
        'Intended Audience :: Information Technology',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: MIT License',
        'Operating System :: Microsoft :: Windows',
        'Programming Language :: Python',
        'Topic :: Software Development :: Build Tools',
        'Topic :: Games/Entertainment',
        'Topic :: Scientific/Engineering :: Artificial Intelligence',
    ],
    package_data={'vgamepad': [
        'win/vigem/client/x64/ViGEmClient.dll',
        'win/vigem/client/x86/ViGEmClient.dll',
        'win/vigem/install/x64/ViGEmBusSetup_x64.msi',
        'win/vigem/install/x86/ViGEmBusSetup_x86.msi',
    ]}
)
