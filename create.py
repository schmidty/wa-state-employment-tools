#!/usr/bin/env python3
#
# This application updates the ESD-job-search-log-251110_Accessible.pdf file
#
import argparse
import datetime, shutil, sys
import pymupdf
import re

from pathlib import Path

from datetime import date, timedelta, datetime
from urllib.parse import unquote, unquote_plus
from pprint import pprint

# PDF to use
original_pdf = "ESD-job-search-log-251110_Accessible.pdf"
name_ssn_object = None
activities = {1: "Employer#20contact", 2: "WorkSource#20activity", 3: "Other#20activity"}




def validate_datetime_string(d: str):
    """Validate the value is a string given"""
    if d == "" or len(d) != 8:
        return datetime.now().strftime("%Y%m%d")
    return d


def get_start_of_week(d: str = "") -> str:
    """Get previous Sunday date as YYYYmmdd
    given today's date.
    """
    fmt = "%Y%m%d"
    d = validate_datetime_string(d)
    do = datetime.strptime(d, fmt).date()
    days_since_sunday = (do.weekday() + 1) % 7
    sunday = do - timedelta(days=days_since_sunday)
    return sunday.strftime(fmt)


def get_end_of_week(d: str = "%Y%m%d", fmt: str = "%Y%m%d") -> str:
    """Get next Saturday date as YYYYmmdd
    given today's date.
    """
    d = validate_datetime_string(d)
    do = datetime.strptime(d, "%Y%m%d").date()
    days_ahead = (5 - do.weekday()) % 7
    return (do + timedelta(days=days_ahead)).strftime(fmt)


def get_contact(contact_num: int, n: int) -> str:
    """Given a number get the contact type
    with the default being 'by-email'.
    NOTE: we are not including 'Other' in this choice set.
    """
    default = f"By email {contact_num}"
    if int(n) > 5 or int(n) < 1:
        return default
    match n:
        case 1:
            if contact_num == 1:
                default = f"In-person {contact_num}"
            elif contact_num == 2:
                default = f"In-person"
            else:
                default = f"In-person-{contact_num}"
        case 2:
            if contact_num < 3:
                default = f"Online {contact_num}"
            else:
                default = f"Online-{contact_num}"
        case 3:
            if contact_num < 3:
                default = f"By phone {contact_num}"
            else:
                default = f"By phone-{contact_num}"
        case 5:
            if contact_num < 3:
                default = f"By mail {contact_num}"
            else:
                default = f"By mail-{contact_num}"
        case 4 | 0:
            if contact_num == 3:
                default = f"By email-{contact_num}"
            else:
                return default  # by-email
    return default


def get_contact_type(contact_num: int, n: int) -> str:
    """Given a number get the 'contact type'"""
    default = "Application#2Fresume"
    if contact_num == 1:
        default = "Application#2FResume#201"

    if int(n) > 3 or int(n) < 1:
        return default
    match n:
        case 1 | 0:
            return default  # "application-resume"
        case 2:
            default = "Interview"
        case 3:
            default = "Inquiry"
    return default


def remove_character(c, v: str) -> str:
    """Remove the character c in a v string"""
    return v.replace(c, " ")


def interactive_employer_contact(data, contact_num: int):
    """This function asks all the 'employer contact' information
    in the ESD-job-search-log-251110_Accessible.pdf document.
    """
    print("\n")
    data[f"Contact date {contact_num} (MM/DD/YYYY)"] = input(
        "What date was this contact made [MM/DD/YYYY, default=today]? "
    ) or datetime.now().strftime("%m/%d/%Y")
    data[f"Job title or job reference number {contact_num}"] = input(
        "Job title or job reference number: "
    )
    data[f"Employer or business name {contact_num}"] = input(
        "Employer or business name: "
    )
    make_contact = (
        input(
            "How did you make the contact? \n\t1. In Person\n\t2. Online\n\t3. By Phone\n\t4. By Email\n\t5. By Mail\n\t6. Other\n"
        )
        or 2
    )

    # Get contact information or by "Other"
    if make_contact == 6:
        data[f"Other {contact_num}"] = input("Describe 'Other': ")
    else:
        contact_1 = get_contact(args.contact_number, make_contact)
        print(contact_1)
        data[contact_1] = True

    contact_type = (
        input(
            "Type of Contact? \n\t1. Application/Resume\n\t2. Interview\n\t3. Inquiry\n"
        )
        or 1
    )

    # Type of contact
    if contact_num == 1:
        data[f"Type of contact (Choose one)"] = get_contact_type(contact_num, contact_type)
    else:
        data[f"Type of contact {contact_num} Choose 1"] = get_contact_type(contact_num, contact_type)

    # Employer information
    data[f"Employer address {contact_num}"] = input("Company Address: ")
    data[f"City {contact_num}-1"] = input("Company City: ")
    data[f"State {contact_num}-1"] = (
        input("Company State [WA=Washington]: ") or "WA"
    )
    data[f"Website or email address {contact_num}"] = input(
        "Company Email or Website: "
    )
    data[f"Phone number {contact_num}"] = input(
        "Company Phone number: "
    )

    # Check answers
    print(
        "\nYou made the following choices. Should answers be used?\n===================================="
    )

    for k, v in data.items():
        if v != "" or v == True:
            match k:
                case s if re.search(r" 1$", s):
                    print(f"{k.replace(' 1', '')}  :{v}:")
                case s if re.search(r" \d\-\d", s):
                    print(f"{k[:-4]}  :{v}:")
                case _:
                    print(f"{k}  :{unquote(v)}:")


    commit = (
        input("====================================\nUse this? [y=Yes/N=No] ") or "n"
    )
    if commit == "y":
        return data
    print("Exiting...")
    sys.exit(1)


def split_up_name(v: str) -> str:
    """This function will accept an input string value only
    and split up the value and return as "Lastname, FirstName MiddleName"
    """
    if v == "":
        return ""
    parts = v.split()
    return f"{parts[2]}, {parts[0]} {parts[1]}"


def search_for_existing_file(d: str) -> str:
    """This function searches for an existing filename 'ESD-job-search-log-20261115_20261121.pdf'
    by date given and returns the filename else it returns a None.
    """
    ret = None
    search_dir = Path("./")
    start = get_start_of_week(d)
    end = get_end_of_week(d)
    potential_filename = f"ESD-job-search-log-{start}_{end}.pdf"
    for file_path in search_dir.rglob(potential_filename):
        return file_path
    return ret


def ask_name_ssn(data: dict[str, str]) -> dict[str, str]:
    """This function asks for your fullname and SSN and returns both as an object."""
    data["Name (Last, First, Middle)"]= input("What is your first, middle and last name? ") or die(
        "ERROR: This is a required input."
    )
    data["ID or SSN"]= input("What is your social security number (with hyphens)? ") or die(
        "ERROR: This is a required input."
    )
    data["Name (Last, First, Middle)"] = split_up_name(data["Name (Last, First, Middle)"])

    print("\n")
    print(f"Name  :{data['Name (Last, First, Middle)']}:")
    print(f"SSN   :{data['ID or SSN']}:")

    yn = input("Does this look accurate? [y=yes, N=no, default=N] ") or "N"
    if yn == "N":
        print("Not accurate. Exiting...")
        sys.exit(1)
    return data


def set_font(f):
    """Set the font size one half more than what it currently is at."""
    # if widget.field_type == pymupdf.PDF_WIDGET_TYPE_TEXT:
    ## If text_fontsize is 0, the PDF viewer auto-scales the text.
    ## Fall back to a sensible default (like 12) before adding 1.
    # current_size = widget.text_fontsize if widget.text_fontsize > 0 else 12
    # widget.text_fontsize = current_size + parseFloat(0.5)
    # widget.update()
    return widget


def parse_args(today: date, argv: list[str] | None = None) -> argparse.Namespace:
    """ This function is set up as middleware for testing and configuration """
    parser = argparse.ArgumentParser("Create a ESD job search log for the week.")
    parser.add_argument(
        "-d",
        "--date",
        default=today,
        help="The start date given for the week or today. This will create the start of the weekday for Sunday in the filename with default being today's date.",
    )
    parser.add_argument("-f", "--filepath", help="The PDF file to edit.")
    parser.add_argument(
        "-c",
        "--contact_number",
        default=1,
        help="Which of the three which contact numbers to use if just updating a single contact.",
    )
    parser.add_argument(
        "-a",
        "--activity",
        default=1,
        help="The contact activity for this edit. [1=Employer activity, 2=WorkSource activity, 3=Other activity, default=1]",
    )
    parser.add_argument(
        "-x",
        "--extract",
        action="store_true",
        help="This will extract and debug the field information for the PDF.",
    )
    parser.add_argument(
        "-z",
        "--fonts",
        action="store_true",
        help="This will extract and debug the font information for the PDF.",
    )
    return parser.parse_args(argv)




# RUN IT: cli arguments
if __name__ == "__main__":
    today = date.today()
    args = parse_args(today.strftime("%Y%m%d"))

    # variables to set
    new_doc = False
    data = {}
    display_input = {}

    # Setup new PDF, use existing PDF or use argument filepath given by user for PDF.
    existing = search_for_existing_file(args.date)
    if existing is not None:
        original_pdf = existing
    elif args.filepath:
        original_pdf = args.filepath
    else:
        new_filename = f"ESD-job-search-log-{get_start_of_week(args.date)}_{get_end_of_week(args.date)}.pdf"
        shutil.copy2(original_pdf, new_filename)
        original_pdf = new_filename
        new_doc = True

    # load the data input fields
    doc = pymupdf.open(original_pdf)

    # Debug font information.
    if args.fonts:
        # Get PDF doc font information
        page = doc[0]
        blocks = page.get_text("dict")["blocks"]
        for block in blocks:
            if block["type"] == 0:  # 0 indicates a text block (1 is an image block)
                for line in block["lines"]:
                    for span in line["spans"]:
                        text = span["text"]
                        font_size = span["size"]
                        font_name = span["font"]
                        print(
                            f"Size: {font_size:.2f} | Font: {font_name} | Text: {text}"
                        )
        sys.exit(1)


    # Debug PDF inputs.
    count = 0
    if args.extract:
        print("\n=======\nHeader:\n=======")

    for page_num, page in enumerate(doc):
        # for widget in page.widgets() or ():
        for widget in page.widgets():

            # NOTE: Set up variables which is needed for the functionality. 
            # This is for the data updates.
            data[widget.field_name] = ""
            # This is for referenning. I could have done one object but it seemed like it would be complex. This is much simpler.
            display_input[widget.field_name] = widget.field_type

            if args.extract:
                if widget.field_name.lower()[0:12] == "contact date":
                    count +=1
                    print(f"\n==========\nContact {count}:\n==========")
                    
                if widget.field_name[0:30] == "What activity did you complete":
                    print("\n")

                if widget.field_type_string == 'RadioButton':
                    print(
                        f"page_num {page_num + 1}, field_name :{widget.field_name}:, field_type :{widget.field_type_string}:, button_states :{widget.button_states()}:"
                    )
                else:
                    print(
                        f"page_num {page_num + 1}, field_name :{widget.field_name}:, field_type :{widget.field_type_string}:, field_value :{widget.field_value}:"
                    )

    if args.extract:
        sys.exit(1)


    # Get personal information of unemployed user filling out this form and set today's date.
    if new_doc:
        data = ask_name_ssn(data)
        original_pdf = new_filename
        data["job-search-week (MM/DD/YYYY)"] = get_end_of_week(today.strftime("%Y%m%d"), "%m/%d/%Y")


    # Set up interactive questions for this PDF.
    match args.activity:
        case 1:  # Employer activity
            data = interactive_employer_contact(data, args.contact_number)
        case 2:  # WorkSource activity
            print("run worksource")
        case 3:  # Other activity
            print("run other")


    # Set activity type
    data[f'Activity type {args.activity}'] = True


    # @TODO: remove this printout of a formatted dictionary
    pprint(data, indent=4)


    # Update the document
    for page_num, page in enumerate(doc):
        for widget in page.widgets():
            # Radio buttons
            if widget.field_type == pymupdf.PDF_WIDGET_TYPE_RADIOBUTTON:
                if  widget.field_name in data and data[widget.field_name] == True and widget.on_state() == activities[args.activity]:
                    widget.field_value = widget.on_state()
                    widget.update()
                    print(f"updated radiobutton activity {widget.field_name}")
                #elif widget.field_name[0:15] == 'Type of contact' and data[widget.field_name] != "" and widget.on_state() == data[widget.field_name]:
                elif widget.field_name[0:15] == 'Type of contact' and data[widget.field_name] != "":
                    print(f"checking :{widget.field_name}: with :{data[widget.field_name]}: == :{widget.on_state()}:")
                    if widget.on_state() == data[widget.field_name]:
                        widget.field_value = widget.on_state()
                        widget.update()
                        print(f"updated radiobutton type of contact {widget.field_name} with {data[widget.field_name]} == {widget.on_state()}")
                    else:
                        widget.field_value = False
                        widget.update()

                else:
                    widget.field_value = False
                    widget.update()
            
            # Check boxes
            elif widget.field_type == pymupdf.PDF_WIDGET_TYPE_CHECKBOX and data[widget.field_name] != "" and widget.field_value == "":
                widget = set_font(widget)
                widget.field_value = data[widget.field_name]
                widget.update()
                print(f"updated input field {widget.field_name}")

            # Standard fields
            elif widget.field_type == pymupdf.PDF_WIDGET_TYPE_TEXT and data[widget.field_name] != "" and widget.field_value == "":
                widget = set_font(widget)
                widget.field_value = data[widget.field_name]
                widget.update()
                print(f"updated input field {widget.field_name}")

    print(f"saving {original_pdf}...")
    doc.save(original_pdf, incremental=True, encryption=pymupdf.PDF_ENCRYPT_KEEP)
    doc.close()
