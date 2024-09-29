import re
from urllib.parse import urlparse
import requests
import os
from logger import main_logger, ignore_logger


# Function to sanitize file names
def sanitize_filename(filename: str) -> str:
    # Replace illegal characters with underscore
    sanitized = re.sub(r'[<>:"/\\|?*]', "_", filename)
    # Remove leading and trailing whitespace
    sanitized = sanitized.strip()
    return sanitized


# TODO: This function needs to be reworked to indicate success or failure
# Function to download a file from a URL
def download_file(file_info: tuple[str, str], access_token: str) -> None:
    file_url, save_path = file_info
    headers = {"Authorization": f"Bearer {access_token}"}
    main_logger.debug(f"Downloading file from: {file_url} at {save_path}")
    response = requests.get(file_url, headers=headers)
    if response.status_code == 200:
        with open(save_path, "wb") as f:
            f.write(response.content)
        main_logger.debug(f"Downloaded: {save_path}")
    else:
        main_logger.error(f"Failed to download file from {file_url}")
        ignore_logger.error(f"{file_url}: Couldn't download file")


# TODO: This function needs to be reworked to indicate success or failure
def save_html(page_url, html_content, course_name):
    parsed_url = urlparse(page_url)
    sanitized_filename = parsed_url.path.replace("/", "_") + ".html"
    save_path = os.path.join("courses", course_name, "cv_pages", sanitized_filename)
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    with open(save_path, "w", encoding="utf-8") as f:
        f.write(html_content)
    main_logger.debug(f"Saved page content: {save_path}")
    return save_path


# Function to save the content of a page to a file, it is saved as  HTML from the body parameter of the page response
# Reference: https://canvas.instructure.com/doc/api/pages.html
def save_page_content(content, save_path):
    with open(save_path, "w", encoding="utf-8") as f:
        f.write(content)
    main_logger.debug(f"Saved page content to: {save_path}")


# Function to fetch the content of a page using its URL
# Reference: https://canvas.instructure.com/doc/api/pages.html
def get_page_content(page_url, access_token):
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(page_url, headers=headers)
    if response.status_code == 200:
        return response.text  # Return the full HTML content of the page
    else:
        main_logger(
            f"Failed to fetch content for page {page_url}: {response.status_code}"
        )
        return ""


# TODO: This function should either be decomposed or reworked to be merged with description
# Function to save the grade and comments for a submission to a text file
# Reference: https://canvas.instructure.com/doc/api/submissions.html
def save_grade_and_comments(file_path, submission):
    grade = submission.get("grade", "No grade")
    score = submission.get("score", "No score")
    comments = submission.get("submission_comments", [])

    with open(file_path, "w") as f:
        f.write(f"Grade: {grade}\n")
        f.write(f"Score: {score}\n\n")
        if comments:
            f.write("Comments:\n")
            for comment in comments:
                f.write(f"- {comment.get('comment', '')}\n")
        else:
            f.write("No comments available.\n")


# Function to save the assignment description to a text file
# Reference: https://canvas.instructure.com/doc/api/assignments.html
def save_assignment_description(file_path, description):
    if description:
        with open(file_path, "w") as f:
            f.write(description)
        main_logger.debug(f"Saved assignment description to: {file_path}")
    else:
        main_logger.debug(f"No description available for the assignment.")
