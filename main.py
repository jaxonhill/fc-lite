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
    pprint.pprint(diversity_course_spans)


if __name__ == "__main__":
    main()
