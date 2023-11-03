import pprint
import re
from urllib.parse import urlparse, parse_qs
from bs4 import BeautifulSoup, Tag
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.remote.webdriver import WebDriver
import pandas as pd

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


def get_urls(course_options_dict: dict, driver: WebDriver) -> list[str]:
    # Regular expression pattern
    pattern = r"https://cmsweb\.cms\.sdsu\.edu(.+?)\'"

    # Create urls list that will hold all class URLs for requests later
    urls = []

    for department, number_list in course_options_dict.items():
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

    return urls


def get_class_info_from_urls(urls: list[str], driver: WebDriver) -> dict:
    # Final Info dict, keys are the column names, values are arrays with respective info
    final_info = {
        "class": [],
        "class_info": [],
        "room": [],
        "dates_times": [],
        "instructor": [],
    }

    for url in urls:
        # Go to the page corresponding to the url
        driver.get(url)

        # Wait for the <tbody> to load and get the table body element
        try:
            tbody = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "ps_grid-body"))
            )
        except Exception:
            continue

        # Wait for a <tr> to load, might be causing problems without this
        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "ps_grid-row"))
            )
        except Exception:
            continue

        # Get the class name
        class_name_element = driver.find_element(
            By.CSS_SELECTOR, "#SSR_CRSE_INFO_V_SSS_SUBJ_CATLG"
        )
        class_name: str = str(class_name_element.text)
        print(class_name)

        # Get the class info
        class_info_element = driver.find_element(
            By.CSS_SELECTOR, "#SSR_CRSE_INFO_V_COURSE_TITLE_LONG"
        )
        class_info: str = str(class_info_element.text)

        # Get all instructor td elements
        instructor_tds = tbody.find_elements(By.CSS_SELECTOR, "td.INSTRUCTOR")
        # For each row of instructors
        for td in instructor_tds:
            curr_instructors: list[str] = []
            spans = td.find_elements(By.TAG_NAME, "span")
            for span in spans:
                curr_instructors.append(str(span.text))
            # APPEND CLASS NAME ONLY HERE
            final_info["class"].append(class_name)
            final_info["class_info"].append(class_info)
            final_info["instructor"].append(curr_instructors)

        # Get all dates_times td elements
        dates_times_tds = tbody.find_elements(By.CSS_SELECTOR, "td.DAYS_TIMES")
        # For each row of dates
        for date_td in dates_times_tds:
            curr_dates_times: list[str] = []
            date_spans = date_td.find_elements(By.TAG_NAME, "span")
            for date_span in date_spans:
                curr_dates_times.append(str(date_span.text))
            final_info["dates_times"].append(curr_dates_times)

        # Get all room td elements
        room_tds = tbody.find_elements(By.CSS_SELECTOR, "td.ROOM")
        # For each row of dates
        for room_td in room_tds:
            curr_rooms: list[str] = []
            room_spans = room_td.find_elements(By.TAG_NAME, "span")
            for room_span in room_spans:
                curr_rooms.append(str(room_span.text))
            final_info["room"].append(curr_rooms)

    return final_info


def main() -> None:
    # Get explorations diversity course options (too many to manually create dictionary)
    explor_divers_course_options: dict = get_explorations_diversity_class_options()

    # Create selenium driver (will remain constant throughout program)
    driver = webdriver.Chrome()
    driver.maximize_window()

    # Go to main page URL
    driver.get(
        "https://cmsweb.cms.sdsu.edu/psc/CSDPRD/EMPLOYEE/SA/c/SSR_STUDENT_FL.SSR_CLSRCH_MAIN_FL.GBL/search"
    )

    # Click Spring 2024
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.LINK_TEXT, "Spring 2024"))
    ).click()

    # Print out all the dictionaries
    pprint.pprint(explor_divers_course_options)
    pprint.pprint(CS_ELECTIVES)
    pprint.pprint(CS_CORE)

    # Get URLs for classes in respective dictionary
    explor_divers_urls = get_urls(explor_divers_course_options, driver)
    cs_elective_urls = get_urls(CS_ELECTIVES, driver)
    cs_core_urls = get_urls(CS_CORE, driver)

    # Get the class info
    diversity_dict = get_class_info_from_urls(explor_divers_urls, driver)
    cs_elective_dict = get_class_info_from_urls(cs_elective_urls, driver)
    cs_core_dict = get_class_info_from_urls(cs_core_urls, driver)

    # Create pandas dataframes
    explorations_diversity_df = pd.DataFrame.from_dict(diversity_dict)
    cs_elective_df = pd.DataFrame.from_dict(cs_elective_dict)
    cs_core_df = pd.DataFrame.from_dict(cs_core_dict)

    # Save the dfs to csv files
    explorations_diversity_df.to_csv("explorations_diversity_options.csv")
    cs_elective_df.to_csv("cs_elective_options.csv")
    cs_core_df.to_csv("cs_core_options.csv")

    # Store all info for each class option using pandas
    # Add a "requirement", is it Explorations, CS Elective, CS Core Class?
    # Get RateMyProfessor ratings
    # Match up professor names
    # Get ratings, might be multiple depending on multiple professors, so create an average rating
    # Sort by average rating
    # Filter out classes that are online?


if __name__ == "__main__":
    main()
