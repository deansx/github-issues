"""gh_issues.py is a module that contains the classes and functions used
by the gh-issues script.

CLASSES:
    ConfigData - holds configuration information for the run

FUNCTIONS:
    calc_moving_avgs
    day_ctr
    date_str2csv_date
    gen_datestr
    gen_datestr
    gen_datetime
    get_config_data
    get_issue_page
    github_issues - Primary driving function
    handle_issues
    update_issue_table
    wait_it_out

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

from collections import defaultdict
from collections import deque
from time import sleep

from . import gh_shared


REPO_BASE = "https://api.github.com/repos/"
PARAMS = [("state", "all"),("per_page", "100")]
MOVING_AVG_WINDOW = 30 # specified in terms of days
AVG_SUFX = "_mov_avg"


# General Outline:
#
# 1. Set up default dict keyed on date string, with entries for create cnt and
#     close cnt
# 2. for each issue:
#     a. on default dict entry for create date increment create count by one
#     b. if state=="closed" on default dict entry for close date, increment
#         close cnt by one
# 3. Now we have a dictionary of all changes.
# 4. Sort the dictionary by date.
# 5. Initialize the running counter to 0
# 6. Starting from the earliest date string, convert to a date, then increment
#     daily. For each day:
#     a. query the default dict for the create & closed counts
#     b. add create count to running counter
#     c. subtract close count from running counter
#     d. write csv with the date and the running count


class ConfigData(object):
    """Contains configuration information.  Allows defaults and processing
    after the config dictionary is loaded.

    Attributes:
        All attributes are strings with (hopefully) self-evident functionality
    """
    def __init__(self):
        self.out_path = "./gh-issues.csv"
        self.repo_owner = None
        self.repo_name = None
        self.username = None
        self.password = None

    def __repr__(self):
        return gh_shared.get_repr(self, "ConfigData")

    def __str__(self):
        return gh_shared.get_str(self, "Configuration Data:", 12)


def day_ctr():
    """Factory function to create a default entry for the defaultdict that
    holds data about the issues we process.
    Returns:
        A dictionary representing the default data for the issue_table entry
    """
    return {'created':0, 'closed':0}


def date_str2csv_date(date_str):
    """Utility function to convert a JSON date string into a date that
    is consistent with the representation in the csv files we work with.
    Args:
        date_str - the Python date string
    Returns:
        A date string formatted for csv
    """
    return ''.join([date_str[:4], date_str[5:7], date_str[8:10]])


def update_issue_table(issue_list, issue_table, results):
    """Main function processing incoming issues to build the issue_table.
    First, determines whether the item is a pull_request, or an issue. If the
    latter, extracts creation date, and, if closed, attempts to extract the
    closed_at date. Performs appropriate format conversions, updates the
    issue table entry for the date(s) involved and updates the results
    counters.
    Args:
        issue_list - list of JSON-like issues from the RESTful API
        issue_table - dictionay keyed by date that we use to collect the
                        the counts of issues opened/closed
        results - a collection of counters that represent open/closed & 
                        issues/pull_requests
    Returns:
        issue_table - updated by this function, allowed since this is a 
                        collection and Python is pass-by-object-reference
        results - updated by this function, allowed since this is a 
                        collection and Python is pass-by-object-reference
    """
    for issue in issue_list:
        results["total_items"] += 1
        if not "pull_request" in issue:
            results["total_issues"] += 1
            results["open_issues"] += 1
            issue_table[date_str2csv_date(issue["created_at"])]["created"] += 1
            if issue["state"] == "closed":
                if issue["closed_at"] is not None:
                    key = date_str2csv_date(issue["closed_at"])
                    issue_table[key]["closed"] += 1
                    results["open_issues"] -= 1
                else:
                    fstr = ("{0}Issue: {1} state is 'closed', but no close "
                            "date is specified - skipping...")
                    print(fstr.format(gh_shared.ERR_LABEL, issue))

        else:
            results["pull_requests"] += 1
    
    results["closed_issues"] = results["total_issues"] - results["open_issues"]


def gen_datetime(date_str):
    """Utility function to convert a YYYYmmdd date string into a Python date
    object.
    Args:
        date_str - the date string
    Returns:
        A Python date object based on the date_str
    """
    return datetime.datetime.strptime(date_str, "%Y%m%d")


def gen_datestr(date):
    """Utility function to convert a Python date object into a YYYYmmdd date
    string that is consistent with the representation in the csv files we 
    work with.
    Args:
        date_str - the Python date string
    Returns:
        A date string formatted as YYYYmmdd for the csv files that we work with
    """
    return date.strftime("%Y%m%d")


def gen_output(out_file, issue_table):
    """Generates the csv output file by running through the issue_table in
    date order and writing a row for each date in the table.
    Args:
        out_file - file handle for the output file. The file is actually
                    opened elsewhere
        issue_table - dictionay keyed by date that we use to collect the
                        the counts of issues opened/closed
    """
    oneday = datetime.timedelta(days=1)
    if len(issue_table.keys()) > 0:
        start_dt = gen_datetime(min(issue_table.keys()))
        end_dt = gen_datetime(max(issue_table.keys()))
        csvout = csv.writer(out_file)
        headers = ["Date", "Created",     "Closed",     "Open",
                           "Created_Avg", "Closed_Avg", "Open_Avg"
                  ]
        csvout.writerow(headers)
        fields = ["created", "closed", "open"]
        fields.extend([f+AVG_SUFX for f in fields])
        open_issues = 0
        curr_dt = start_dt
        while curr_dt <= end_dt:
            curr_dts = gen_datestr(curr_dt)
            data = issue_table[curr_dts]
            created = data["created"]
            closed = data["closed"]
            open_issues = open_issues + created - closed
            row = [data[f] for f in fields]
            row.insert(0,curr_dts)
            csvout.writerow(row)
            curr_dt += oneday
    else:
        print(''.join([NOTE_LABEL, "No issues logged, nothing to output."]))

    out_file.close


def calc_moving_avgs(issue_table, window):
    """Calculates the moving average for each of the data fields in the
    issue table.
    Args:
        issue_table - dictionay keyed by date that we use to collect the
                        the counts of issues opened/closed
        window - integer specifying the number of days to use as the 
                        moving "window" - generally 30, but you can 
                        experiment with different periods to suit your
                        data sets
    """
    oneday = datetime.timedelta(days=1)
    winf = float(window)
    if len(issue_table.keys()) > 0:
        # The fields that we'll calculating averages for.
        fields = ["closed", "created", "open"]

        # We need to keep track of a "window's" worth of values for each
        # field, so we'll use a dictionary. One of the dictionary keys is
        # a counter that we use to make sure that we have enough values
        # to calculate the average across the specified window
        run_avg = {"counter":0}

        for f in fields:
            # Initialize the data for each field. We'll keep track of
            # both the current value of the moving average and the last
            # "window" number of daily values
            # Note that the deque is initialized with a 0.0 value, this
            # will be popped when the moving average is actually
            # calculated for the first time.
            run_avg[f] = {"curr_avg":0.0, "past_vals":deque([0.0])}

        def calc_avgs(data_dict):
            """Updates the moving average for all fields based on a row of
            data from the issue_table.
            Args:
                data_dict - dictionary representing one "row" from the 
                            issue_table
            """
            run_avg["counter"] += 1
            for f in fields:
                # for this field, the new_val is the data divided
                # by the size of the average window
                new_val = float(data_dict[f])/winf
                ra = run_avg[f]
                # add new_val to the running average field and push
                # new_val onto the past values
                ra["curr_avg"] += new_val
                ra["past_vals"].appendleft(new_val)
                
                if run_avg["counter"] >= window:
                    ra["curr_avg"] -= ra["past_vals"].pop()
                    data_dict[f+AVG_SUFX] = ra["curr_avg"]
                else:
                    # still building the past_vals FIFO, so
                    # no moving average in the data
                    data_dict[f+AVG_SUFX] = None
        # Initialize values, including the start / end keys for the
        # issue_table
        start_dt = gen_datetime(min(issue_table.keys()))
        end_dt = gen_datetime(max(issue_table.keys()))
        open_issues = 0
        curr_dt = start_dt
        while curr_dt <= end_dt:
            curr_dts = gen_datestr(curr_dt)
            data = issue_table[curr_dts]
            created = data["created"]
            closed = data["closed"]
            open_issues = open_issues + created - closed
            data["open"] = open_issues
            calc_avgs(data)
            curr_dt += oneday
    else:
        slst = [ gh_shared.NOTE_LABEL
                ,"No issues logged, nothing to calculate."
               ]
        print(''.join(slst))


def wait_it_out(msg, total_wait):
    """If our access to the repo's REST api is being rate limited, we might
    need to pause for a while to wait for our next allocation of requests.
    This function periodically let's the user know that we're still waiting
    while it waits until we can download issues again.
    Args:
        msg - str with the message to display while we're waiting
        total_wait - duration of the wait in seconds. We'll periodically
                        issue a note to the console during the wait so that
                        the user knows that we haven't died, yet...
    """
    total_wait += 15
    wait_incr = 240
    fstrlst = ["{0}{1}\n      ", "{2}", " minutes remaining..."]
    while total_wait >= 0:
        if total_wait > 60:
            mins = total_wait // 60
        else:
            mins = total_wait / 60
            fstrlst[1] = "{1:0.2f}"
        fstr = ''.join(fstrlst)
        print(fstr.format(gh_shared.NOTE_LABEL, msg, mins))
        sleep(wait_incr if total_wait > wait_incr else total_wait)
        total_wait -= wait_incr

    print(''.join([ gh_shared.NOTE_LABEL
                   ,"Wait completed, continuing execution..."
                  ]))


def get_issue_page(url, params, auth):
    """Get a page of issues from the GitHub REST api
    Args:
        url - str containing the url to request
        params - list of tuples containing the parameters to accompany the
                    request
        auth - either a tuple of two strings that will be user/pwd for
                    authentication, or None
    Returns:
        The page of issues, if successful.
        Waits if we are rate limited
        Raises an exception if the status code has some other unsuccessful
        value
    """
    response = requests.get(url, params=params, auth=auth)
    if response.headers["x-ratelimit-remaining"] == "0":
        print("Rate Limit Hit, waiting for reset...")
        reset = int(response.headers["x-ratelimit-reset"])
        reset_at = datetime.datetime.utcfromtimestamp(reset)
        wait_time = (reset_at - datetime.datetime.utcnow()).seconds
        print("Resets at: {}".format(reset_at))
        print("Currently: {}".format(datetime.datetime.utcnow()))
        print("Waiting:   {} minutes".format(wait_time // 60))
        wait_it_out("Rate Limit Hit", wait_time)
        return get_issue_page(url, params, auth)
    elif response.status_code == 200:
        return response
    else:
        raise Exception(response.status_code)


def handle_issues(url, params, auth, issue_table, results):
    """Main loop for fetching the issues from the GitHub REST API. Retrieves
    a page at a time, until it gets back a bad status, or runs through all
    of the issues pages.
    Args:
        url - str containing the url to request
        params - list of tuples containing the parameters to accompany the
                    request
        auth - either a tuple of two strings that will be user/pwd for
                    authentication, or None
        issue_table - dictionay keyed by date that we use to collect the
                        the counts of issues opened/closed
        results - a collection of counters that represent open/closed & 
                        issues/pull_requests
    Returns:
        issue_table - updated by this function, allowed since this is a 
                        collection and Python is pass-by-object-reference
        results - updated by this function, allowed since this is a 
                        collection and Python is pass-by-object-reference
    """
    total_recs = 0
    while url is not None:
        response = get_issue_page(url, params, auth)
        recs = len(response.json())
        total_recs += recs
        fstr = "Processing {0} issues/pull requests, for {1} total"
        print(fstr.format(recs, total_recs))
        update_issue_table(response.json(), issue_table, results)
        if "link" in response.headers:
            pages = dict(
                [(reln[6:-1], ref[ref.index('<')+1:-1]) for ref, reln in
                 [refs.split(';') for refs in
                  response.headers['link'].split(',')]])
            if "last" in pages and "next" in pages:
                url = pages["next"]
            else:
                url = None
        else:
            url = None
    

def github_issues(config_data):
    """Primary function of the script. Orchestrates getting the issues,
    calculating the moving averages and generating the output of the program
    Args:
        config_data - object containing processed configuration information
    """
    # The api returns both reported issues and pull requests as issues, so we
    # have to separate them during processing
    # Of course, total_issues == total_created issues, the open_issues entry is
    # most meaningful when dumping the issues from GitHub. It's not as important
    # for the issue_table
    results = {"pull_requests":0
               ,"total_issues":0
               ,"open_issues":0
               ,"closed_issues":0
               ,"total_items":0
               }
    # By using a defaultdict, we'll have "data" even for days where there are
    # no issues created/closed
    issue_table = defaultdict(day_ctr)

    url = "".join([REPO_BASE
                   ,config_data.repo_owner
                   ,"/"
                   ,config_data.repo_name
                   ,"/issues"
                   ])
    if config_data.username is not None and config_data.password is not None:
          auth = (config_data.username, config_data.password)
    else:
          nstr = ("No authentication will be used. This will work, albeit "
                  "slowly, for public repos.")
          print(''.join([gh_shared.NOTE_LABEL, nstr]))
          auth = None

    handle_issues(url, PARAMS, auth, issue_table, results)

    calc_moving_avgs(issue_table, MOVING_AVG_WINDOW)

    gen_output(config_data.out_file, issue_table)

    fstr = ("Total items:     {0}\n"
            "Total issues:    {1}\n"
            "      Open issues:   {2}\n"
            "      Closed issues: {3}\n"
            "Total pull reqs: {4}\n")
    print(fstr.format(results["total_items"]
                      ,results["total_issues"]
                      ,results["open_issues"]
                      ,results["closed_issues"]
                      ,results["pull_requests"]))


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

    # Make sure that we have the repo owner/name information
    if config_data.repo_owner is None or config_data.repo_name is None:
        fstr = ("{0}Your configuration must specify both an owner and a "
                "name for the target GitHub repository.\n{1}")
        print(fstr.format(gh_shared.ERR_LABEL, gh_shared.EXITING_STR))
        sys.exit(1)

    # Open the output file, we'll exit here if there's a problem, rather
    # than downloading the data, and then crashing. Also, this will lock
    # the file handle
    try:
        config_data.out_file = open(config_data.out_path, 'w', newline='')
    except FileNotFoundError as fnf:
        fstr = "{0}Unable to create output file\n{1}{2}\n{3}"
        print(fstr.format( gh_shared.ERR_LABEL
                          ,gh_shared.ERR_INDENT
                          ,fnf
                          ,gh_shared.EXITING_STR
                         ))
        sys.exit(1)
    except PermissionError as prm:
        fstr = "{0}Incorrect access rights to output file\n{1}{2}\n{3}"
        print(fstr.format( gh_shared.ERR_LABEL
                          ,gh_shared.ERR_INDENT
                          ,prm
                          ,gh_shared.EXITING_STR
                         ))
        sys.exit(1)

    return config_data

