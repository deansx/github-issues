"""gh_merge.py maps contains the classes and functions used by the
gh-merge script

CLASSES:
    ConfigData - holds configuration information for the run

FUNCTIONS:
    get_config_data
    github_merge - Primary driving function
    load_issues

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
import csv
import requests
import datetime
import argparse
import configparser

from collections import defaultdict

from . import gh_shared


# General Outline:
#
# 1. Open the issues.csv file and read it into a dictionary
# 2. Initialize the open issues counter
# 3. Open the entropy file and read it as regular CSV.  For each row
#     a. look up the associated entry (key on date) in the issues dict, using
#         get() with a default of {"Created":None, "Closed":None, "Open":None}
#     b. dump the row to the merged csv file, with the original headings
#         from the entropy file + 
#         ["Created", "Closed", "Open"]
# 


class ConfigData(object):
    """Contains configuration information.  Allows defaults and processing
    after the config dictionary is loaded.

    Attributes:
        All attributes are strings with (hopefully) self-evident functionality
    """
    def __init__(self):
        self.entropy_path = "./entropy.csv"
        self.issues_path = "./gh-issues.csv"
        self.merged_path = "./gh-entropy-issues.csv"

    def __repr__(self):
        return gh_shared.get_repr(self, "ConfigData")

    def __str__(self):
        return gh_shared.get_str(self, "Configuration Data:", 16)


def load_issues(issues_path):
    """Opens the csv file containing GitHub issue data and loads it into a
    row based table where the keys are the date of the data.
    Args:
        issues_path - str containing the pathname to the issues csv file
    Returns
        The new date indexed table of issue data
    """
    issues_dict = {}
    with open(issues_path) as issues:
        issue_rdr = csv.DictReader(issues)
        for row in issue_rdr:
            issues_dict[row["Date"]] = row

    return issues_dict


def github_merge(config_data):
    """Primary function of the script. Loads both the entropy data and the
    issues data. Next, using keys from the Date field of the entropy file, 
    pulls out the fields of interest from the issues table and merges the new
    data into the row data from the entropy file.  Finally, the merged row is
    written to the specified output csv file.
    Args:
        config_data - object containing processed configuration information
    """
    issues = load_issues(config_data.issues_path)
    with open(config_data.entropy_path) as entropy:
        entropy_rdr = csv.reader(entropy)
        with open(config_data.merged_path, 'w', newline='') as merge:
            merge_wrtr = csv.writer(merge)
            entropy_hdrs = next(entropy_rdr)
            issue_hdrs = ["Created",     "Closed",     "Open",
                          "Created_Avg", "Closed_Avg", "Open_Avg"
                         ]
            merge_hdrs = entropy_hdrs + issue_hdrs
            merge_wrtr.writerow(merge_hdrs)
            default_i = {}
            for k in issue_hdrs:
                default_i[k] = None
            for e_row in entropy_rdr:
                i = issues.get(e_row[0], default_i)
                i_row = [i[k] for k in issue_hdrs]
                e_row.extend(i_row)
                merge_wrtr.writerow(e_row)
                                      
    print("Generated: {0}".format(config_data.merged_path))


def get_config_data(config_file_path):
    """Loads the configuration data, if possible, then loads the data into
    an instance of this module's ConfigData class. This allows us to set 
    defaults and to process configuration info.  We also dumped opening the
    output file into this function so that we can be relatively sure that
    everything that we need, from a configuration standpoint is available and
    valid when we run the script.
    Args:
        config_file_path - str with the path to the config file
    Returns:
        A populated instance of the ConfigData object
    """
    config_data = ConfigData()
    gh_shared.load_config_data(config_file_path, config_data)
    return config_data
