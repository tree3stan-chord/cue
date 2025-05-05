# cue  
(noun) : cue one up with that Spatzula  
(see also) : WiP; but what isn't?  
(see also also) : something clever (x4) later


## what is this?  

bit of a wannabe DSP playground but with your hands (hot {pink,green}.gloves not included).  
I've tried to link in the DSP in Fortran90 for educative reasons.  

Have fun with that.  
(If you choose. I'm not forcing you to do anything ;))

### tinkering for yourself  
all the usual `clone`ing and so on.  

Check my `.tool-versions` for python version.  

I recommend a version manager like `asdf`.  
I also recommend using a `venv` after you've isolated a version: `python -m venv .cuenv`  and then activate it with `source .cuenv/bin/activate`.   
or whatever name you want to give the venv. venv[^1].  

Until I improve this thing[^2]:
~~**build the fortran extensions in-place**~~
~~`python setup.py build_ext --inplace`~~
~~unless you modify the fortran modules, you shouldn't have to run this again.~~
~~But if you modify the fortran modules, you should run this again.~~


~~**Install the package**~~
~~`pip install .`~~


~~**Running the thing**~~
~~thanks to that nonsense above, you can just run `gesture-dsp` from your shell, provided you're in an environment you `pip install`ed into.~~


**I sort of improved the thing:**  
If you trust me, use the makefile:  
do the venv things and then `make build && make install`.  

In normal dev flow, `make clean || make uninstall` to clean up the environment a bit.  


If you find yourself testing interpreter things, you can still do `python3 -m gesture_dsp.cli [args...]`.  
You can also just do `python3 -m gesture_dsp [args...]` due to the dunder.



[^1]: Venv. It's fun to say.
[^2]: I improved the thing in the sense that there's a makefile wrapping that nonsense now.