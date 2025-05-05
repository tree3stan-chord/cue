.PHONY: build install clean

# compile all Fortran extensions in-place
build:
	python3 setup.py build_ext --inplace --verbose

# Build then install the package (rebuilding console scripts)
install: build
	pip install --force-reinstall .

# run this thang (no impulse rspnse)
run:
	python3 -m gesture_dsp.cli wavy.wav

# run this thang (yes impulse rspnse)
irrun:
	python3 -m gesture_dsp.cli wavy.wav --ir impulse_response.wav

# Remove all build artifacts and compiled modules
clean:
	rm -rf build/ dist/ *.egg-info
	rm -rf src/gesture_dsp.egg-info
	rm -rf src/gesture_dsp/dsp_effects/*.{so,mod}
	rm -rf __pycache__ */__pycache__

uninstall: clean
	python3 -m pip uninstall gesture_dsp