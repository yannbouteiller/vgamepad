from setuptools import setup, find_packages
from os import path
import platform

assert platform.system() == 'Windows', "Sorry, this module is only compatible with Windows so far."

with open(path.join(path.abspath(path.dirname(__file__)), 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='vgamepad',
    version='0.0.1',
    description='Virtual XBox360 and DualShock4 gamepads in python',
    long_description=long_description,
    url='https://github.com/yannbouteiller/vgamepad',
    author='Yann Bouteiller',
    author_email='',
    license='MIT',
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
    keywords='virtual gamepad python xbox dualshock controller',
    packages=find_packages(),
    package_data={'vgamepad': [
        'win/vigem/client/x64/ViGEmClient.dll',
        'win/vigem/client/x86/ViGEmClient.dll',
        'win/vigem/install/x64/ViGEmBusSetup_x64.msi',
        'win/vigem/install/x86/ViGEmBusSetup_x86.msi',
    ]}

)
