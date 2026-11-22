#!/usr/bin/env python3
#
# This application updates the ESD-job-search-log-251110_Accessible.pdf file
#
import argparse
import datetime, shutil, sys
import pymupdf, os
import re, importlib

from pathlib import Path

from datetime import date, timedelta, datetime
from urllib.parse import unquote, unquote_plus
from pprint import pprint

# PDF to use
original_pdf = "ESD-job-search-log-251110_Accessible.pdf"
name_ssn_object = None
activities = {1: "Employer#20contact", 2: "WorkSource#20activity", 3: "Other#20activity"}



def check_python_version(test_version: float | None = 0) -> bool | str:
    """ This function checks the python version required
        to run this script else it returns an error
        and exits.
    """
    exception_message = "This script requires Python 3.10 or higher."
    if test_version > 0:
        return exception_message
    try:
        if sys.version_info < (3, 10):
            raise RuntimeError(exception_message)
    except RuntimeError as r:
        print("Error:", r)
        sys.exit(1)
    return True

def is_module_installed(module_name: str) -> bool:
    """ Checks if module is installed else returns None """
    return importlib.util.find_spec(module_name) is not None


def check_python_packages_installed() -> bool:
    """ This function checks that the non-native
        packages are installed to run this application.
    """
    required = ["pymupdf", "pytest"]
    missing = [pkg for pkg in required if not is_module_installed(pkg)]
    if missing:
        print(f"missing modules: {', '.join(missing)}")
    return True


def validate_datetime_string(d: str):
    """Validate the value is a string given"""
    if d == "" or len(d) != 8:
        return datetime.now().strftime("%Y%m%d")
    return d


def get_start_of_week(d: str = "") -> str:
    """Get previous Sunday date as YYYYmmdd
    given today's date.
    """
    if d == "":
        return d
    fmt = "%Y%m%d"
    do = datetime.strptime(d, fmt)
    days_since_sunday = (do.weekday() + 1) % 7
    sunday = do - timedelta(days=days_since_sunday)
    return sunday.strftime(fmt)


def get_end_of_week(d: str = "", fmt: None | str = "%Y%m%d") -> str:
    """ Get next Saturday date as YYYYmmdd given today's date. """
    if d == "":
        return d
    do = datetime.strptime(d, "%Y%m%d")
    days_ahead = (5 - do.weekday()) % 7
    if days_ahead == 0: # if the date is Saturday then be strict about it.
        days_ahead = 7
    next_sat = do + timedelta(days=days_ahead)
    return next_sat.strftime(fmt)


def get_contact(contact_num: int, n: int) -> str:
    """Given a number get the contact type with the default being 'by-email'.
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


def interactive_other(data: dict[str, str], contact_num: int) -> dict[str, str]:
    """This function asks all the 'other activity' information
       in the ESD-job-search-log-251110_Accessible.pdf document.
    """
    data[f"What activity did you complete {contact_num}-2"] = input("What activity did you complete? ") or ""
    data[f"What documentation do you have {contact_num}-2"] = input("What documentation do you have? ") or ""
    yn = input("Does this look accurate [y=yes, n=no, default=n]? ") or "n"
    if yn == "y":
        return data

    return None


def interactive_worksource(data: dict[str, str], contact_num: int) -> dict[str, str] | None:
    """This function asks all the 'worksource activity' information
       in the ESD-job-search-log-251110_Accessible.pdf document.
    """
    data[f"What activity did you complete {contact_num}-1"] = input("What activity did you complete? ") or ""
    data[f"What documentation do you have {contact_num}-1"] = input("What documentation do you have? ") or ""
    data[f"Where did you complete this activity {contact_num}"] = input("Where did you complete this activity? ") or ""
    data[f"City {contact_num}-2"] = input("What city? [default=Spokane]") or "Spokane"
    data[f"State {contact_num}-2"] = input("What state [default=WA]? ") or "WA"
    yn = input("Does this look accurate [y=yes, n=no, default=n]? ") or "n"
    if yn == "y":
        return data
    # Incorrect entries as decided by the user... if new file then delete it.
    return None


def interactive_employer_contact(data: dict[str, str], contact_num: int) -> dict[str, str] | None:
    """This function asks all the 'employer contact' information
       in the ESD-job-search-log-251110_Accessible.pdf document.
    """
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
    data[f"City {contact_num}-1"] = input("Company City [default=Spokane]: ") or "Spokane"
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

    # Verify entries (we show raw keys and values here)
    for k, v in data.items():
        if v != "" or v == True:
            print(f"{remove_numbers(k)}  :{display_activity(v)}:")

    commit = (
        input("====================================\nUse this? [y=Yes/N=No] ") or "n"
    )
    if commit == "y":
        return data
    # Incorrect entries as decided by the user... if new file then delete it.
    return None



def interactive_get_contact_date(data: dict[str, str], contact_num: int) -> dict[str, str] | None:
    """ Ask the user for the contact date of these entries """
    contact_date = f"Contact date 1 (MM/DD/YYYY)"
    if contact_num == 2:
        contact_date = f"Contact Date 2 MMDDYYYY"
    elif contact_num == 3:
        contact_date = f"Contact date (MM/DD/YYYY)"
    print("\n")
    today_formatted = datetime.now().strftime("%m/%d/%Y")
    data[contact_date] = input(
        f"What date was this contact made [MM/DD/YYYY, default={today_formatted}]? "
    ) or today_formatted
    #pprint(data, indent=4)
    print(f"You stated :{data[contact_date]}:")
    yn = input("Does this look accurate [y=yes, n=no, default=n]? ") or "n"
    if yn == "y":
        return data
    # Incorrect entries as decided by the user... if new file then delete it.
    return None


def display_activity(v: str) -> str:
    """ redisplay the activity and remove ugly formatting values """
    match v:
        case "Application#2FResume#201":
            return "Application Resume"
        case "Application#2Fresume#201":
            return "Application Resume"
        case "Employer#20contact":
            return "Employer Contact"
        case "Employer#20Contact":
            return "Employer Contact"
        case "WorkSource#20Activity":
            return "WorkSource Activity"
        case "WorkSource#20activity":
            return "WorkSource Activity"
        case _:
            return v
    return v

def remove_numbers(k: str) -> str:
    """ This removes the numbers in a string value like '1', '1-1', '2-1', '2-2', '3-1', '3-2'
    when displaying the company's address information; it cleans it up
    """
    return re.sub(r"[0-9\-]{0,3}", "", k, count=0).strip()

def split_up_name(v: str) -> str:
    """This function will accept an input string value only
    and split up the value and return as "Lastname, FirstName MiddleName"
    """
    if v == "":
        return ""
    parts = v.split()
    return f"{parts[2]}, {parts[0]} {parts[1]}"


def remove_pdf_file(f:str):
    """ Delete a PDF file by given filepath """
    if f == "":
        print("PDF filepath not given. Try again...")
        return False
    try:
        if os.path.exists(f):
            yn = input(f"PDF file found.\nAre you sure you want to delete file '{f}'?\nOnce deleted it is gone!\n[y=yes, default=no] ")
            if yn == "y":
                Path(f).unlink(missing_ok=True)
                print(f"PDF file {f} has been deleted.")
            else:
                print("Exiting...")
        else:
            raise Exception(f"file does not exist: {f}")
    except ValueError as e:
        print("error: ", e)


def search_for_existing_file(d: str) -> str:
    """This function searches for an existing filename 'ESD-job-search-log-20261115_20261121.pdf'
    by date given and returns the filename else it returns a None.
    """
    ret = None
    if str == "":
        return None
    search_dir = Path("./")
    start = get_start_of_week(d)
    end = get_end_of_week(d)
    potential_filename = f"ESD-job-search-log-{start}_{end}.pdf"
    for file_path in search_dir.rglob(potential_filename):
        return file_path
    return ret

def check_header_not_filled_in(d: dict[str, str]) -> bool:
    """ This function checks to see if the header values 'job-search-week (MM/DD/YYYY)', 
    'Name (Last, First, Middle)' and 'ID or SSN' have been filled in with the existing
    document and if not returns False else True
    """
    return d['job-search-week (MM/DD/YYYY)'] == "" and d['Name (Last, First, Middle)'] == "" and d['ID or SSN'] == ""


def ask_name_ssn(data: dict[str, str]) -> dict[str, str] | None:
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

    yn = input("Does this look accurate? [y=yes, n=no, default=n] ") or "n"
    if yn == "y":
        return data
    # If no data returned that means the user did not accept the entries. If a new PDF document then delete it.
    sys.exit(1)


def set_font_size(widget: pymupdf.Widget, font_size: float=0.5) -> pymupdf.Widget:
    """Set the font size is set. If it currently greater than zero then add to the size else subtract from it. """
    if widget.field_type == pymupdf.PDF_WIDGET_TYPE_TEXT:
        # If text_fontsize is 0, the PDF viewer auto-scales the text.
        # Fall back to a sensible default (like 12) before adding 1.
        #current_size = widget.text_fontsize if widget.text_fontsize > 0 else 12
        if args.overwrite:
            return widget  # We don't want the font to get bigger
        if widget.text_fontsize > 0:
            current_size = widget.text_fontsize
            widget.text_fontsize = current_size + float(font_size)
        else:
            current_size = 12
            widget.text_fontsize = current_size - float(font_size)
        widget.update()
    return widget


def parse_args(today: date, argv: list[str] | None = None) -> argparse.Namespace:
    """ This function is set up as middleware for testing and configuration """
    parser = argparse.ArgumentParser("Create a ESD job search log for the week.")
    parser.add_argument(
        "-t",
        "--today",
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
        "-o",
        "--overwrite",
        action='store_true',
        help="Overwrite existing PDF document. WARNING: This is a dangerous command with an existing PDF document!",
    )
    parser.add_argument(
        "-r",
        "--remove",
        help="Delete a PDF files by filepath. Example: python create.py --remove 'ESD-job-search-log-20261122_20261128.pdf' ",
    )
    parser.add_argument(
        "-x",
        "--extract",
        action="store_true",
        help="This will extract and debug the field information for the PDF.",
    )
    parser.add_argument(
        "-d",
        "--debug",
        action="store_true",
        help="This will debug the application where debug statements are set.",
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
    check_python_version()
    check_python_packages_installed()
    today = date.today()
    args = parse_args(today.strftime("%Y%m%d"))

    # variables to set
    new_doc = False
    data = {}
    display_input = {}

    # remove pdf file
    if args.remove:
        remove_pdf_file(args.remove)
        sys.exit(0)

    # Setup new PDF, use existing PDF or use argument filepath given by user for PDF.
    existing = search_for_existing_file(args.today)
    if existing is not None:
        original_pdf = existing
    elif args.filepath:
        original_pdf = args.filepath
    else:
        new_filename = f"ESD-job-search-log-{get_start_of_week(args.today)}_{get_end_of_week(args.today)}.pdf"
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
            data[widget.field_name] = widget.field_value if widget.field_value != "" else ""
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
    if check_header_not_filled_in(data):
        data = ask_name_ssn(data)
        data["job-search-week (MM/DD/YYYY)"] = get_end_of_week(today.strftime("%Y%m%d"), "%m/%d/%Y")


    # Set up interactive questions for this PDF.
    data = interactive_get_contact_date(data, int(args.contact_number))
    if data is None and new_doc:
        print("Exiting...")
        sys.exit(1)

    match args.activity:
        case "1":  # Employer activity
            print("\nQuestions for 'Employer Activity':")
            data = interactive_employer_contact(data, int(args.contact_number))
        case "2":  # WorkSource activity
            print("\nQuestions for 'WorkSource Activity':")
            data = interactive_worksource(data, int(args.contact_number))
        case "3":  # Other activity
            print("\nQuestions for 'Other Activity':")
            data = interactive_other(data, int(args.contact_number))

    # If no data returned that means the user did not accept the entries. If a new PDF document then delete it.
    if data is None and new_doc:
        print("Exiting...")
        sys.exit(1)


    # Set activity type
    data['Activity type 1'] = True

    # @TODO: remove this printout of a formatted dictionary
    #pprint(data, indent=4)

    # Update the document
    for page_num, page in enumerate(doc):
        for widget in page.widgets():
            # Radio buttons
            if widget.field_type == pymupdf.PDF_WIDGET_TYPE_RADIOBUTTON:
                if  widget.field_name in data and data[widget.field_name] == True and widget.on_state() == activities[int(args.activity)]:
                    widget.field_value = widget.on_state()
                    widget.update()
                    print(f"updated radiobutton activity {widget.field_name}")
                #elif widget.field_name[0:15] == 'Type of contact' and data[widget.field_name] != "" and widget.on_state() == data[widget.field_name]:
                elif widget.field_name[0:15] == 'Type of contact' and data[widget.field_name] != "":
                    #print(f"checking :{widget.field_name}: with :{data[widget.field_name]}: == :{widget.on_state()}:")
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
            elif widget.field_type == pymupdf.PDF_WIDGET_TYPE_CHECKBOX and data[widget.field_name] != "" and (widget.field_value == "" or args.overwrite == True):
                widget = set_font_size(widget, 3) # Subtract from size
                widget.field_value = data[widget.field_name]
                widget.update()
                print(f"updated input field {widget.field_name}")

            # Standard fields
            elif widget.field_type == pymupdf.PDF_WIDGET_TYPE_TEXT and data[widget.field_name] != "" and (widget.field_value == "" or args.overwrite == True):
                widget = set_font_size(widget, 3) # Subtract from size
                widget.field_value = data[widget.field_name]
                widget.update()
                print(f"updated input field {widget.field_name}")
            elif args.debug and data[widget.field_name] != "":
                print(f"FAILED field key :{widget.field_name}:, value :{data[widget.field_name]}:")



    print(f"saving {original_pdf}...")
    doc.save(original_pdf, incremental=True, encryption=pymupdf.PDF_ENCRYPT_KEEP)
    doc.close()

