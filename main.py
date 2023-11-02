import pprint
import re
from bs4 import BeautifulSoup, Tag
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.remote.webelement import WebElement

# Create dictionaries of CS electives and CS core classes that I still have to take
CS_ELECTIVES = {
    "CS": [
        "470",
        "497",
        "498",
        "503",
        "514",
        "530",
        "532",
        "537",
        "545",
        "546",
        "549",
        "553",
        "556",
        "558",
        "559",
        "561",
        "562",
        "572",
        "574",
        "576",
        "577",
        "581",
        "578",
        "582",
        "596",
    ]
}
CS_CORE = {
    "CS": [
        "420",
        "450",
        "460",
        "480",
    ],
    "STAT": [
        "550",
    ],
}


def filter_condition(span: Tag) -> bool:
    return span["number"][-1] == "+"


def course_name_filter_condition(element: WebElement, number_list: list[str]):
    return (
        element.find_element(By.CLASS_NAME, "ps-link")
        .find_elements(By.TAG_NAME, "b")[1]
        .text
        in number_list
    )


def get_explorations_diversity_class_options() -> dict:
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
        department: str = span["department"].strip()
        curr_class_number: str = span["number"].replace("+", "").strip()

        # If the department already exists in the dictionary, append to the array
        if department in course_department_number_dict.keys():
            course_department_number_dict[department].append(curr_class_number)
        else:
            course_department_number_dict[department] = [curr_class_number]

    return course_department_number_dict


def main() -> None:
    # Get explorations diversity course options
    explor_divers_course_options: dict = get_explorations_diversity_class_options()

    # Open selenium
    driver = webdriver.Chrome()
    driver.maximize_window()
    driver.get(
        "https://cmsweb.cms.sdsu.edu/psc/CSDPRD/EMPLOYEE/SA/c/SSR_STUDENT_FL.SSR_CLSRCH_MAIN_FL.GBL/search"
    )

    # Click Spring 2024
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.LINK_TEXT, "Spring 2024"))
    ).click()

    # Regular expression pattern
    pattern = r"https://cmsweb\.cms\.sdsu\.edu(.+?)\'"

    # Create urls list that will hold all class URLs for requests later
    urls = []

    for department, number_list in explor_divers_course_options.items():
        # Navigate based on department dictionary using URL f-string
        driver.get(
            f"https://cmsweb.cms.sdsu.edu/psc/CSDPRD/EMPLOYEE/SA/c/SSR_STUDENT_FL.SSR_CLSRCH_ES_FL.GBL?Page=SSR_CLSRCH_ES_FL&SEARCH_GROUP=SSR_CLASS_SEARCH_LFF&SEARCH_TEXT=%&ES_INST=SDCMP&ES_STRM=2243&ES_ADV=Y&ES_SUB={department}&ES_CNBR=&ES_LNAME=&KeywordsOP=CT&SubjectOP=EQ&CatalogNbrOP=CT&LastNameOP=CT&GBLSRCH=PTSF_GBLSRCH_FLUID"
        )

        # Wait for table to load
        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "win0divPTS_RSLTS_GB"))
            )
        except:
            continue

        # Get all <li> with class rowact (this holds information for each course option)
        li_elements = driver.find_elements(By.CLASS_NAME, "psc_rowact")

        matching_li_elements: list[WebElement] = []

        # Loop through li elements and check if there is a match on the course number
        for element in li_elements:
            if course_name_filter_condition(element, number_list):
                matching_li_elements.append(element)

        if matching_li_elements:
            for match in matching_li_elements:
                regex_match = re.search(pattern, match.get_attribute("onclick"))
                if regex_match:
                    end_of_url = regex_match.group(1)
                    urls.append("https://cmsweb.cms.sdsu.edu" + end_of_url)

    pprint.pprint(urls)

    # Store all info for each class option using pandas
    # Add a "requirement", is it Explorations, CS Elective, CS Core Class?
    # Get RateMyProfessor ratings
    # Match up professor names
    # Get ratings, might be multiple depending on multiple professors, so create an average rating
    # Sort by average rating
    # Filter out classes that are online?


if __name__ == "__main__":
    main()
