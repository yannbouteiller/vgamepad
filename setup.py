from setuptools import setup, find_packages
import platform
from pathlib import Path
import subprocess
import sys
import warnings

assert platform.system() == 'Windows', "Sorry, this module is only compatible with Windows so far."

archstr = platform.machine()
if archstr.endswith('64'):
    arch = "x64"
elif archstr.endswith('86'):
    arch = "x86"
else:
    if platform.architecture()[0] == "64bit":
        arch = "x64"
    else:
        arch = "x86"
    warnings.warn(f"vgamepad could not determine your system architecture: \
                  the vigembus installer will default to {arch}. If this is not your machine architecture, \
                  please cancel the upcoming vigembus installation and install vigembus manually from \
                  https://github.com/ViGEm/ViGEmBus/releases/tag/setup-v1.17.333")

pathMsi = Path(__file__).parent.absolute() / "vgamepad" / "win" / "vigem" / "install" / arch / ("ViGEmBusSetup_" + arch + ".msi")

# Prompt installation of the ViGEmBus driver (blocking call)
if sys.argv[1] != 'egg_info' and sys.argv[1] != 'sdist':
    subprocess.call(['msiexec', '/i', '%s' % str(pathMsi)], shell=True)

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name='vgamepad',
    packages=[package for package in find_packages()],
    version='0.0.7',
    license='MIT',
    description='Virtual XBox360 and DualShock4 gamepads in python',
    long_description=long_description,
    long_description_content_type="text/markdown",
    author='Yann Bouteiller',
    url='https://github.com/yannbouteiller/vgamepad',
    download_url='https://github.com/yannbouteiller/vgamepad/archive/refs/tags/v0.0.7.tar.gz',
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
