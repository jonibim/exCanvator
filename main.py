import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from dotenv import load_dotenv
import json
from api import CanvasAPIClient
from crawler import CanvasCrawler
from endpoints import COURSE_FRONTPAGE_ENDPOINT, COURSES_ENDPOINT
from functions import (
    download_file,
    get_page_content,
    save_assignment_description,
    save_grade_and_comments,
    save_page_content,
)

from logger import main_logger, api_logger, crawl_logger


# Load environment variables from .env file
load_dotenv()

# Retrieve environment variables
CANVAS_ACCESS_TOKEN = os.getenv("CANVAS_ACCESS_TOKEN")
CANVAS_DOMAIN = os.getenv("CANVAS_DOMAIN")
CANVAS_API_URL = f"https://{CANVAS_DOMAIN}/api/v1"
CRAWLER_WORKERS = os.getenv("CRAWLER_WORKERS")

download = False

# TODO: Obviously this also needs to be refactored and functions need to be merged
# TODO: Preferably add test files


# Main function to download assignment details, submissions, and save results
def download_assignments_and_submissions(
    client: CanvasAPIClient, course_id: str, course_name: str, workers: int = 1
):
    # Get all assignments for the course
    assignments = client.get_assignments(course_id)
    if not assignments:
        main_logger.warning(f"No assignments found for course: {course_name}")
        return

    file_downloads = []  # List to hold all file download tasks

    for assignment in assignments:
        assignment_name = assignment.get("name", "Unnamed_Assignment").replace("/", "_")
        assignment_id = assignment["id"]
        main_logger.debug(f"  Assignment: {assignment_name} (ID: {assignment_id})")

        # Create directory structure for the assignment
        course_dir = os.path.join(
            "courses", course_name, "cv_assignments", assignment_name
        )
        os.makedirs(course_dir, exist_ok=True)

        # Save assignment description if available
        description = assignment.get("description", None)
        description_file_path = os.path.join(course_dir, "assignment_description.txt")
        save_assignment_description(description_file_path, description)

        # Download any attached files in the assignment description
        if "attachments" in assignment and assignment["attachments"]:
            for attachment in assignment["attachments"]:
                file_name = attachment["display_name"].replace("/", "_")
                file_url = attachment["url"]
                save_path = os.path.join(course_dir, file_name)
                file_downloads.append((file_url, save_path))

        # Fetch submission details
        submission = client.get_submission(course_id, assignment_id)
        if submission:
            # Download any files attached to the submission
            if "attachments" in submission and submission["attachments"]:
                for attachment in submission["attachments"]:
                    file_name = attachment["display_name"].replace("/", "_")
                    file_url = attachment["url"]
                    save_path = os.path.join(course_dir, f"submission_{file_name}")
                    file_downloads.append((file_url, save_path))

            # Save grade and comments to a text file
            result_file_path = os.path.join(course_dir, "assignment_result_score.txt")
            save_grade_and_comments(result_file_path, submission)
        else:
            main_logger.warning(
                f"    No submission found for assignment: {assignment_name}"
            )

    # Parallel downloading of files
    if file_downloads:
        with ThreadPoolExecutor(max_workers=workers) as executor:
            futures = [
                executor.submit(download_file, file_info, client.access_token)
                for file_info in file_downloads
            ]

            # Wait for all futures to complete
            for future in as_completed(futures):
                future.result()  # This will raise an exception if any download failed
    else:
        main_logger.warning(f"  No files to download for course: {course_name}")


def download_all_files(
    client: CanvasAPIClient, course_id: str, course_name: str, workers: int = 1
):
    # Get all files for the course
    files = client.get_files(course_id)
    if files:
        main_logger.info(f"Found {len(files)} files for course: {course_name}")

        # Create a directory only if there are files
        course_dir = os.path.join("courses", course_name)
        os.makedirs(course_dir, exist_ok=True)

        # Prepare file info for parallel downloading
        file_downloads = [
            (
                file["url"],
                os.path.join(course_dir, file["display_name"].replace("/", "_")),
            )
            for file in files
        ]

        # Use ThreadPoolExecutor to download files in parallel
        with ThreadPoolExecutor(max_workers=workers) as executor:
            futures = [
                executor.submit(download_file, file_info, client.access_token)
                for file_info in file_downloads
            ]

            # Wait for all futures to complete
            for future in as_completed(futures):
                future.result()  # This will raise an exception if any download failed
    else:
        main_logger.warning(f"No files found for course: {course_name}")


# Main function to download files from modules in all courses
def download_files_from_modules(
    client: CanvasAPIClient, course_id: str, course_name: str, workers: int = 1
):

    # Get all modules for the course
    modules = client.get_modules(course_id)
    if not modules:
        main_logger.warning(f"No modules found for course: {course_name}")
        return

    # List to hold all files that need to be downloaded
    file_downloads = []
    external_links = []

    for module in modules:
        module_name = module.get("name", "Unnamed_Module").replace("/", "_")
        module_id = module["id"]
        main_logger.debug(f"  Module: {module_name} (ID: {module_id})")

        # Get all items in the module
        module_items = client.get_module_items(course_id, module_id)
        if not module_items:
            main_logger.warning(f"    No items found in module: {module_name}")
            continue

        for item in module_items:
            # Check the type of item
            item_type = item["type"]

            # TODO: Needs to be same implementation as crawler
            if item_type == "File":
                # Handle file attachments
                file_name = item["title"].replace("/", "_")
                file_id = item["content_id"]
                file_response = client.get_course_files(course_id, file_id)
                file_obj = file_response.json()
                # Prepare the download directory for the course and module
                course_dir = os.path.join(
                    "courses", course_name, "cv_modules", module_name
                )
                os.makedirs(course_dir, exist_ok=True)

                url = file_obj["url"]
                if url == "":
                    main_logger.error(f"Can't download {file_obj['display_name']}")
                    main_logger.error(f"  File ID: {file_id}")
                    main_logger.error(f"  File URL: {url}")
                    main_logger.error(f"  f{json.dumps(file_obj)}")

                    # Also save the file info to a separate file
                    no_download_links_path = os.path.join(
                        "courses", course_name, "cv_modules", "cant_download.txt"
                    )
                    with open(no_download_links_path, "w") as f:
                        f.write(json.dumps(file_obj) + "\n")
                else:
                    save_path = os.path.join(course_dir, file_name)
                    file_downloads.append((url, save_path))

            elif item_type == "ExternalUrl":
                # Save external links
                external_link = item["external_url"]
                external_links.append(external_link)

            # TODO: Needs to be rechecked
            elif item_type == "Page":
                # Handle Canvas pages
                page_url = item["url"]  # Use the page URL provided in the item
                page_title = item["title"].replace("/", "_")
                page_content = get_page_content(page_url, client.access_token)

                # Prepare the page save path
                course_dir = os.path.join(
                    "courses", course_name, "cv_modules", module_name
                )
                os.makedirs(course_dir, exist_ok=True)

                save_path = os.path.join(course_dir, f"{page_title}.txt")
                save_page_content(page_content, save_path)

    # Download files in parallel
    if file_downloads:
        main_logger.debug(f"Downloading {len(file_downloads)} files")
        with ThreadPoolExecutor(
            max_workers=min(workers, len(file_downloads))
        ) as executor:
            futures = [
                executor.submit(download_file, file_info, client.access_token)
                for file_info in file_downloads
            ]

            # Wait for all futures to complete
            for future in as_completed(futures):
                future.result()  # This will raise an exception if any download failed
    else:
        main_logger.warning(
            f"  No files to download in modules for course: {course_name}"
        )

    # Save external links to a file
    if external_links:
        external_links_path = os.path.join("courses", course_name, "external_links.txt")
        with open(external_links_path, "w") as f:
            for link in external_links:
                f.write(link + "\n")
        main_logger.debug(f"Saved external links to: {external_links_path}")


# Main function to download all files for each course
def download_content_from_course(
    client: CanvasAPIClient, crawler: CanvasCrawler, workers: int = 1
):
    courses = client.get_courses()
    if not courses:
        main_logger.warning("No courses found.")
        return

    # for idx, course in enumerate(courses):
    #     course_name = course.get("name", "Unnamed_Course").replace("/", "_")
    #     course_id = course["id"]
    #     print(f"{course_name} : {course_id}")

    for idx, course in enumerate(courses):
        course_name = course.get("name", "Unnamed_Course").replace(
            "/", "_"
        )  # Avoid directory issues with slashes
        course_id = course["id"]

        os.system("cls||clear")

        print(f"Processing: {course_name} ({idx+1}/{len(courses)}) ", end="\r")
        main_logger.info(f"Fetching \nCourse: {course_name} (ID: {course_id})")

        # TODO: User-friendly command line interface with arguments
        # Uncomment one of the following if you want to disable downloading of files
        download_all_files(client, course_id, course_name, workers)
        download_files_from_modules(client, course_id, course_name, workers)
        download_assignments_and_submissions(client, course_id, course_name, workers)

        # Starting points for crawling
        homepage_url = (
            f"{CANVAS_API_URL}{COURSE_FRONTPAGE_ENDPOINT.format(course_id=course_id)}"
        )
        syllabus_url = f"{CANVAS_API_URL}{COURSES_ENDPOINT.format(course_id=course_id)}?include[]=syllabus_body"

        # Start crawling from the homepage
        visited_links = set()  # To avoid re-crawling the same pages
        crawler.crawl_page(homepage_url, visited_links)
        crawler.crawl_page(syllabus_url, visited_links)


# TODO: User-friendly command line interface with arguments
if __name__ == "__main__":
    if not CANVAS_ACCESS_TOKEN or not CANVAS_DOMAIN:
        print("NOTICE: Please set the environment variables for Canvas API access.")
        exit(1)

    if not CRAWLER_WORKERS:
        print("NOTICE: Please set the number of workers for the crawler.")
        exit(1)

    clientAPI = CanvasAPIClient(
        access_token=CANVAS_ACCESS_TOKEN, domain_url=CANVAS_DOMAIN, logger=api_logger
    )

    crawler = CanvasCrawler(clientAPI, logger=crawl_logger)

    download_content_from_course(
        client=clientAPI, crawler=crawler, workers=CRAWLER_WORKERS
    )
