grip-attendance.py
=========================

Introduction / Description
----------------------

github_issues includes a pair of scripts that work together to map GitHub Issues
to the output from the [commit-entropy](https://pypi.python.org/pypi/commit-entropy/0.2.0) program. The output (csv files) from these scripts provides
quick and easy access for charting and further analysis of the correlation
between project entropy and issues reported against the code.

* gh-issues - scans a GitHub repository's issues
then generates a .csv file showing the number of issues created,
closed and total open for each day.

* gh-merge - maps the results from gh-issues.py onto the results
produced commit-entropy. The combined file is indexed by the dates
from commit-entropy and shows the corresponding issue open/close
activity for each day.


Command Line Usage
----------------------

USAGE:

    gh-issues [config_file.cfg] -[Hh][elp]
    gh-merge  [config_file.cfg] -[Hh][elp]

Both programs require a configuration file. A default pathname is checked, if
a pathname isn't specified on the command line.


Configuration File
----------------------

In addition to specifying I/O files, gh-issues needs to be able to
identify the repository where it will extract issues. This script also benefits
from using GitHub credentials to access the API.

Often, we use a single config file for both scripts. A sample file 
[gh-sample.cfg](./gh-sample.cfg) is included. Note, however, that you'll
need to change th username/password information, at least, to actually
use the sample config.

Some things to note about configuration file values - these are all
driven by the environment's configuration processing capabilities:

* Upper/Lower case is important

* Changes made to a section will only apply to processing of that
section's corresponding data file

* Don't use quotes unless absolutely necessary to support trailing
blanks in field names (I don't know why some systems generate field
names with trailing blanks, but they do). Spaces between words are fine,
so values with intra-word blank spaces do not require quotes. If you use
quotes, the quotes will be stripped during the configuration load process


Installation
----------------------

gh-issues and gh-merge currently support [Python 3.x](https://www.python.org/downloads/).
All testing and development was performed on Linux, your mileage on other
platforms may vary. Further, the temporary installation script will only work
in an environment that supports Bash scripting. Sorry about that. I'll do
a pip version ASAP. In the meantime, the installation steps for a Linux
environment are:

    git clone git@github.com:deansx/github-issues.git
    cd github-issues
    ./install.bsh

This script should put the two command files into a directory that is in your
shell's PATH, and the shared modules in a directory that is in your Python
installation's sys.path. You may need to modify it for your specific situation,
and you might need to run it as root.

Support
----------------------

If you have any questions, problems, or suggestions, please submit an
[issue](../../issues)

License & Copyright
----------------------

Copyright 2015 Grip QA

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
