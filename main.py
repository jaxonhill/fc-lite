import requests
import pprint
import re
from bs4 import BeautifulSoup, Tag


def filter_condition(span: Tag) -> bool:
    return span["number"][-1] == "+"


def main() -> None:
    # Open html
    with open("de.html") as html:
        soup = BeautifulSoup(html, "html.parser")

    # Find explorations table and get course spans
    explorations_table = soup.find(
        "table", {"id": "selectcourses-d99bbb23-1271-4ff3-b26a-f81275c0986f"}
    ).find("table")
    course_spans: list[Tag] = list(
        explorations_table.find_all("span", {"class": "draggable"})
    )

    # Filter course spans to get diversity classes with the "+" at the end of the number
    diversity_course_spans: list[Tag] = list(filter(filter_condition, course_spans))

    # Create dictionary of departments and numbers
    course_department_number_dict: dict = {}
    for span in diversity_course_spans:
        # Get current department and class number
        department: str = span["department"]
        curr_class_number: str = span["number"].replace("+", "")

        # If the department already exists in the dictionary, append to the array
        if department in course_department_number_dict.keys():
            course_department_number_dict[department].append(curr_class_number)
        else:
            course_department_number_dict[department] = [curr_class_number]

    pprint.pprint(course_department_number_dict)

    # TODO:
    # Open selenium
    # Click Spring 2024
    # Navigate based on department dictionary using URL f-string
    # Match course names and open them to get class options
    # Store all info for each class option using pandas
    # Add a "requirement", is it Explorations, CS Elective, CS Core Class?
    # Get RateMyProfessor ratings
    # Match up professor names
    # Get ratings, might be multiple depending on multiple professors, so create an average rating
    # Sort by average rating
    # Filter out classes that are online?


if __name__ == "__main__":
    main()
