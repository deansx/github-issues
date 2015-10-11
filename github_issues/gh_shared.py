"""gh_shared is a Python3 shared module to support the GitHub Issues
scripts. Functions include:
  => get_config_data - prepares a configuration object

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
"""

__author__ = "Dean Stevens"
__copyright__ = "Copyright 2015, Grip QA"
__license__ = "Apache License, Version 2.0"
__status__ = "Prototype"
__version__ = "0.1.0"


import sys
import argparse
import configparser

ERR_LABEL = "ERROR: "
NOTE_LABEL = "NOTE: "
ERR_INDENT = ' '*len(ERR_LABEL)
EXITING_STR = ''.join([ERR_INDENT, "Exiting..."])
QUOTE_CHARS = ''.join(["'",'"'])


def repr_list(an_obj):
    # Produce a formatted list of this object's members and their values
    def out_attr(attr):
        # Handles formatting and password display
        rtn_val = None
        if attr != "password":
            rtn_val = "{}:{}".format(attr, getattr(an_obj, attr))
        else:
            ps = "********"
            pwd = ps if getattr(an_obj, "password", None) is not None else None
            rtn_val = "password:{0}".format(pwd)

        return rtn_val

    attr_list = [ out_attr(v) for v in sorted(vars(an_obj))]

    return attr_list


def get_repr(an_obj, label):
    members = repr_list(an_obj)
    members.insert(0,''.join(['<', label]))
    ret_str = ' '.join(members)
    # since we don't want a space before the closing angle bracket
    ret_str = ''.join([ret_str, '>'])
    return (ret_str)


def get_str(an_obj, label, attr_field_len=12):
    def gen_line(av_item):
        # given an attribute:value string, returns a line formatted for
        # __str__ representation in output.
        attr_indent = 3
        av = av_item.split(':')
        sp = attr_field_len-len(av[0])
        return ''.join([' '*attr_indent, av[0], ':', ' '*sp, av[1]])

    lines = [ gen_line(i) for i in repr_list(an_obj)]
    lines.insert(0, label)
    return '\n'.join(lines)


def load_config_data(config_file_path, config_object):
    """Loads the configuration data, if possible, then loads the data into
    an instance of this module's ConfigData class. This allows us to set 
    defaults and to process configuration info.  We also dumped opening the
    output file into this function so that we can be relatively sure that
    everything that we need, from a configuration standpoint is available and
    valid when we run the script.
    Args:
        config_file_path - str with the path to the config file
        config_object - a caller specific object with members that represent
                        items of interest in the configuration dictionary
    Returns:
        config_object - updated by this function, allowed since this is a 
                        an object and Python is pass-by-object-reference
    """
    config = configparser.ConfigParser()
    if config.read(config_file_path):
        fstr = "{0}Using configuration file: '{1}'"
        print(fstr.format(NOTE_LABEL, config_file_path))
    else:
        fstr = "{0}Unable to open configuration file: '{1}'\n{2}"
        print(fstr.format(ERR_LABEL, config_file_path, EXITING_STR))
        sys.exit(1)

    def_config = config["DEFAULT"]

    def strip_quotes(string):
        sstr = string
        if string[0] == string[-1] and string[0] in QUOTE_CHARS:
            string = string[1:-1]
        return string

    for cfg_var in vars(config_object):
        try:
            setattr(config_object, cfg_var, strip_quotes(def_config[cfg_var]))
        except KeyError:
            fstr = "{0}'{1}' not specified in config file, using '{2}'"
            print(fstr.format(NOTE_LABEL
                              ,cfg_var
                              ,getattr(config_object, cfg_var)))


