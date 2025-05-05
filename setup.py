from numpy.distutils.core import setup, Extension
from setuptools import find_packages
import numpy as np
import os

effects = [
    'mid_side', 'convolution_reverb', 'bitcrush',
    'filters', 'granular', 'spectral_freeze',
    'delay', 'pitch_shift',
]

ext_modules = []
for name in effects:
    kwargs = {}
    if name == 'spectral_freeze':
        fftw_prefix = os.environ.get('FFTW_PREFIX', '/opt/homebrew')
        kwargs = {
            'include_dirs': [np.get_include(), f'{fftw_prefix}/include'],
            'library_dirs': [f'{fftw_prefix}/lib'],
            'libraries': ['fftw3'],
            'runtime_library_dirs': [f'{fftw_prefix}/lib'],
            'extra_compile_args': [f'-I{fftw_prefix}/include'],
            'extra_link_args':    [f'-L{fftw_prefix}/lib'],
        }
    ext_modules.append(
        Extension(
            f'gesture_dsp.dsp_effects.{name}',
            [f'src/gesture_dsp/dsp_effects/{name}.f90'],
            **kwargs
        )
    )

setup(
    name='gesture-dsp',
    version='0.1.0',
    package_dir={'': 'src'},
    packages=find_packages('src'),
    ext_modules=ext_modules,
    install_requires=[
        'numpy',
        'opencv-python',
        'pyaudio',
    ],
    entry_points={
        'console_scripts': [
            'gesture-dsp=gesture_dsp.cli:main',
        ]
    }
)