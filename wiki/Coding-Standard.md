## Guidelines
* All code should have tests. Pull requests that modify code should have new tests or modified existing tests to pass. 

* All code should be documented. Write docstrings for all public modules, functions, classes, and methods. [PEP 257](https://www.python.org/dev/peps/pep-0257) and [Google Python Style Guide](http://google.github.io/styleguide/pyguide.html#38-comments-and-docstrings) describe good docstring conventions. 

## Stylistic Guidelines
* Set up your editor to follow [PEP 8](https://www.python.org/dev/peps/pep-0008/) (remove trailing white space, no tabs, etc.). Check code with pyflakes / flake8. [Codecov](https://app.codacy.com/gh/radiome-flow/radiome/dashboard) is set up to check code quality of commits and pull requests.

* [EditorConfig](https://github.com/radiome-flow/radiome/blob/master/.editorconfig) is available to maintain consistent coding styles for multiple developers working on the same project across various editors and IDEs.

* Function annotations([PEP 484](https://www.python.org/dev/peps/pep-0484)) and variable annotations([PEP 526](https://www.python.org/dev/peps/pep-0526)) are recommended to enable more powerful auto-completion and type checking (Example: [Google pytype](https://github.com/google/pytype)).

* Prefer f-strings([PEP 498](https://www.python.org/dev/peps/pep-0498/)) over `%-formatting`, `str.format()`, and `string.Template` to improve readability. 

* Use data structures Radiome provides instead of Python basic data types. (`ResourcePool` instead of `dict`).

## Running the tests

To run tests for the current environment, use
``` 
$ make test
```
You need to have Python 3.6, 3.7, 3.8 and other dependencies to run all of the environments. Then run
```
$ make test-all
```
Check code coverage quickly with the default Python:
```
$ make coverage
```

## Building the docs
Build the docs in the docs directory using `Sphinx`:
```
$ make docs
```








