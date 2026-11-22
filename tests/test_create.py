#!/usr/bin/env python3
import pytest
import os
import pymupdf

from datetime import datetime
from pathlib import Path

from create import get_start_of_week
from create import validate_datetime_string
from create import get_end_of_week
from create import interactive_employer_contact
from create import get_contact
from create import get_contact_type
from create import remove_character
from create import split_up_name
from create import search_for_existing_file
from create import set_font
from create import parse_args

# Functions and variable configs for tests
test_pdf = "ESD-job-search-log-251110_Accessible.pdf"



# Tests
def test_validate_datetime_string():
    """ Validate the datetime given value
        to be a string and 6 characters long
    """
    want = "20261117" # Today
    got  = validate_datetime_string("20261117")
    assert got == want

def test_validate_datetime_string_fails():
    """ Validate the datetime given value
        to be a string and 6 characters long
    """
    #want = "20261117" # Today
    want = datetime.now().strftime("%Y%m%d")
    got  = validate_datetime_string("2026111777")
    assert got == want

def test_get_start_of_week():
    """ tests the function for getting the start of
        the week given the today's date. Example:
            20261117 give should return 20261115 for 
            the previous Sunday.
    """
    want = "20261115" # Sunday
    got  = get_start_of_week("20261117")
    assert got == want

def test_get_start_of_week_no_input():
    """ tests the function for getting the start of
        the week given the today's date. Example:
            "" given should return 20261115 for 
            the previous Sunday.
    """
    want = "20261115" # Sunday
    got  = get_start_of_week("")
    assert got == want

def test_get_start_of_week_input_None():
    """ tests the function for getting the start of
        the week given the today's date. Example:
            None value given should return 20261115 for 
            the previous Sunday.
    """
    want = "20261115" # Sunday
    got  = get_start_of_week()
    assert got == want

def test_get_end_of_week():
    """ tests the function for getting the end of
        the week given the today's date. Example:
            20261117 give should return 20261121 for
            the next Saturday.
    """
    want = "20261121" # Saturday
    got  = get_end_of_week("2026117")
    assert got == want


def test_get_end_of_week_diff_format():
    """ tests the function for getting the end of
        the week given the today's date. Example:
            20261117 give should return 20261121 for
            the next Saturday.
    """
    want = "11/21/2026" # Saturday
    got  = get_end_of_week("2026117", "%m/%d/%Y")
    assert got == want


def test_get_end_of_week_no_input():
    """ tests the function for getting the end of
        the week given the today's date. Example:
            "" given should return 20261121 for
            the next Saturday.
    """
    want = "20261121" # Saturday
    got  = get_end_of_week("")
    assert got == want

def test_get_end_of_week_input_None():
    """ tests the function for getting the end of
        the week given the today's date. Example:
            None value given should return 20261121 for
            the next Saturday.
    """
    want = "20261121" # Saturday
    got  = get_end_of_week()
    assert got == want

def test_get_contact():
    """ test the choice functionality for getting
        the key and values as a JSON object to be updated in the
        'ESD-job-search-log-251110_Accessible.pdf' copy.
    """
    want = "In-person 1"
    got = get_contact(1, 1)
    assert got == want

    want = "Online 1"
    got = get_contact(1, 2)
    assert got == want

    want = "Online 2"
    got = get_contact(2, 2)
    assert got == want

    want = "Online-3"
    got = get_contact(3, 2)
    assert got == want

    want = "By mail 1"
    got = get_contact(1, 5)
    assert got == want

    want = "By mail 1"
    got = get_contact(1, 5)
    assert got == want

    want = "By mail-3"
    got = get_contact(3, 5)
    assert got == want

    want = "By phone-3"
    got = get_contact(3, 3)
    assert got == want

    want = "By phone-3"
    got = get_contact(3, 3)
    assert got == want

    want = "By email 1"
    got = get_contact(1, 0)
    assert got == want

    want = "By email-3"
    got = get_contact(3, 4)
    assert got == want


def test_get_contact_type():
    """ test the contact type returned for given number type """
    want = "Interview"
    got = get_contact_type(1, 2)
    assert got == want
    want = "Application#2FResume#201"
    got = get_contact_type(1, 999)
    assert got == want
    want = "Inquiry"
    got = get_contact_type(1, 3)
    assert got == want
    want = "Application#2FResume#201"
    got = get_contact_type(1, 0)
    assert got == want
    want = "Application#2Fresume"
    got = get_contact_type(2, 1)
    assert got == want
    want = "Application#2Fresume"
    got = get_contact_type(3, 1)
    assert got == want

def test_remove_underline():
    """ Test removing the underline is a string value """
    want = "contact type"
    got = remove_character("_", "contact_type")
    assert got == want
    want = "contact type"
    got = remove_character("_", "contact type")
    assert got == want

def test_split_up_name():
    """ Test the functionality of splitting up a name and redordring the parts """
    want = ""
    got  =  split_up_name("")
    assert got == want
    want = "Cougar, Butch The"
    got  =  split_up_name("Butch The Cougar")
    assert got == want

def test_search_for_existing_file():
    """ This tests the functionality for an existing edited PDF file """
    want = "ESD-job-search-log-20261115_20261121.pdf"
    got = search_for_existing_file("20261118")
    print(got)

def test_parse_args():
    """ This tests the arguments from the command line """
    today = "20261119"
    args = parse_args(today, ["--extract"])
    assert args.extract == True
    

