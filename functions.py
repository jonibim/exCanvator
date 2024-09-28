import json
import re
import time
from urllib.parse import parse_qs, urljoin, urlparse
from bs4 import BeautifulSoup
import requests
import os

# TODO: User environment variables or a configuration file to store these values
CANVAS_DOMAIN = 'canvas.tue.nl'
API_URL = f'https://{CANVAS_DOMAIN}/api/v1'  
ACCESS_TOKEN = '<TOKEN_GOES_HERE>' 

headers = {
    'Authorization': f'Bearer {ACCESS_TOKEN}'
}

# TODO: Use a logger instead of writing to files
with open('error_log.txt', 'w') as f:
    f.write('Error Log\n\n')
    
with open('ignored_links.txt', 'w') as f:
    f.write('Ignored Links\n\n')
    

# Regular expressions to extract file IDs and preview IDs from Canvas URLs
# TODO: More patterns should be added and tested
file_id_pattern = re.compile(r'/files/(\d+)')
preview_id_pattern = re.compile(r'preview=(\d+)')

# TODO: Add more illegal characters
# TODO: Save the pattern as a constant
# Function to sanitize file names
def sanitize_filename(filename):
    # Replace illegal characters with underscore
    sanitized = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # Remove leading and trailing whitespace
    sanitized = sanitized.strip()
    return sanitized


# TODO: Add verbose logging and error handling
# Function to get all courses
# Reference: https://canvas.instructure.com/doc/api/courses.html
def get_courses():
    courses_endpoint = f'{API_URL}/courses'
    courses = []
    page = 1

    while True:
        response = requests.get(courses_endpoint, headers=headers, params={'page': page})
        if response.status_code != 200:
            print(f"Failed to fetch courses: {response.status_code}")
            raise Exception(f"Failed to fetch courses: {response.status_code}")
        
        data = response.json()
        if not data:
            break  # No more courses
        
        courses.extend(data)
        page += 1

    return courses

# TODO: Add verbose logging and error handling
# Function to get all files in a course
# Reference: https://canvas.instructure.com/doc/api/files.html
def get_files(course_id):
    files_endpoint = f'{API_URL}/courses/{course_id}/files'
    files = []
    page = 1

    while True:
        response = requests.get(files_endpoint, headers=headers, params={'page': page})
        if response.status_code != 200:
            print(f"Failed to fetch files for course {course_id}: {response.status_code}")
            return files

        data = response.json()
        if not data:
            break  # No more files

        files.extend(data)
        page += 1

    return files

# TODO: Add verbose logging and error handling
# Function to get all assignments in a course
# Reference: https://canvas.instructure.com/doc/api/assignments.html
def get_assignments(course_id):
    assignments_endpoint = f'{API_URL}/courses/{course_id}/assignments'
    assignments = []
    page = 1

    while True:
        response = requests.get(assignments_endpoint, headers=headers, params={'page': page})
        if response.status_code != 200:
            # TODO: Log the error
            print(f"Failed to fetch assignments for course {course_id}: {response.status_code}")
            return assignments

        data = response.json()
        if not data:
            break  # No more assignments

        assignments.extend(data)
        page += 1

    return assignments

# TODO: Add verbose logging and error handling
# Function to get submission details for an assignment
# Reference: https://canvas.instructure.com/doc/api/submissions.html
def get_submission(course_id, assignment_id):
    submission_endpoint = f'{API_URL}/courses/{course_id}/assignments/{assignment_id}/submissions/self'
    response = requests.get(submission_endpoint, headers=headers)

    if response.status_code == 200:
        return response.json()
    else:
        print(f"Failed to fetch submission for assignment {assignment_id}: {response.status_code}")
        return None

# TODO: Add verbose logging and error handling
# Function to get all modules in a course
# Reference: https://canvas.instructure.com/doc/api/modules.html
def get_modules(course_id):
    modules_endpoint = f'{API_URL}/courses/{course_id}/modules'
    modules = []
    page = 1

    while True:
        response = requests.get(modules_endpoint, headers=headers, params={'page': page})
        if response.status_code != 200:
            print(f"Failed to fetch modules for course {course_id}: {response.status_code}")
            return modules

        data = response.json()
        if not data:
            break  # No more modules

        modules.extend(data)
        page += 1

    return modules
# TODO: Add verbose logging and error handling
# Function to get items in a module
# Reference: https://canvas.instructure.com/doc/api/modules.html#method.context_module_items_api.index
def get_module_items(course_id, module_id):
    items_endpoint = f'{API_URL}/courses/{course_id}/modules/{module_id}/items'
    items = []
    page = 1

    while True:
        response = requests.get(items_endpoint, headers=headers, params={'page': page})
        if response.status_code != 200:
            print(f"Failed to fetch items for module {module_id}: {response.status_code}")
            return items

        data = response.json()
        if not data:
            break  # No more items

        items.extend(data)
        page += 1

    return items

# TODO: Add verbose logging and error handling
# TODO: Merge this function with the download_file_mod function
# Function to download a file from a URL
def download_file(file_info):
    file_url, save_path = file_info
    response = requests.get(file_url, headers=headers)
    if response.status_code == 200:
        with open(save_path, 'wb') as f:
            f.write(response.content)
        print(f"Downloaded: {save_path}")
    else:
        print(f"Failed to download file from {file_url}")
        
# Function to download a file
def download_file_mod(file_url, save_path):
    response = requests.get(file_url, headers=headers)
    if response.status_code == 200:
        with open(save_path, 'wb') as f:
            f.write(response.content)
        print(f"Downloaded: {save_path}")
    else:
        with open('error_log.txt', 'a') as f:
            f.write(f"Failed to download file from {file_url}\n")
        print(f"Failed to download file from {file_url}")

# TODO: This function needs to be reworked
# TODO: Also needs error handling and logging
def save_html(page_url, html_content, course_name):
    parsed_url = urlparse(page_url)
    sanitized_filename = parsed_url.path.replace('/', '_') + '.html'
    save_path = os.path.join('courses', course_name, 'cv_pages', sanitized_filename)
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    with open(save_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    print(f"Saved page content: {save_path}")
    return save_path

# TODO: This function needs to be reworked as well
# Function to save the content of a page to a file, it is saved as  HTML from the body parameter of the page response
# Reference: https://canvas.instructure.com/doc/api/pages.html
def save_page_content(content, save_path):
    with open(save_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Saved page content to: {save_path}")

# Function to fetch the content of a page using its URL
# Reference: https://canvas.instructure.com/doc/api/pages.html
def get_page_content(page_url):
    response = requests.get(page_url, headers=headers)
    if response.status_code == 200:
        return response.text  # Return the full HTML content of the page
    else:
        print(f"Failed to fetch content for page {page_url}: {response.status_code}")
        return ""

# TODO: This function should either be decomposed or reworked to be merged with description
# Function to save the grade and comments for a submission to a text file
# Reference: https://canvas.instructure.com/doc/api/submissions.html
def save_grade_and_comments(file_path, submission):
    grade = submission.get('grade', 'No grade')
    score = submission.get('score', 'No score')
    comments = submission.get('submission_comments', [])

    with open(file_path, 'w') as f:
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
        with open(file_path, 'w') as f:
            f.write(description)
        print(f"Saved assignment description to: {file_path}")
    else:
        print(f"No description available for the assignment.")


# TODO: This hurts my eyes. Needs decoupling and more error handling
# Function to crawl and download files/pages recursively
def crawl_page(page_url, course_name, course_id, visited):
    BASE_URL = f'{API_URL}/courses/{course_id}'
    if page_url in visited:
        return
    visited.add(page_url)

    # Fetch the page content
    response = requests.get(page_url, headers=headers)
   
    if response.status_code != 200:
        print(f"Failed to fetch page: {page_url}")
        response_content_type = response.headers.get('Content-Type')
        response_error_reason = ''
        if response_content_type and 'application/json' in response_content_type:
            response_error_json = response.json()
            response_error_reason = json.dumps(response_error_json.get('errors'))
        with open('error_log.txt', 'a') as f:
            f.write(f"Failed to fetch page: {page_url}\n")
            f.write(f"Course: {course_name}\n")
            f.write(f"Course ID: {course_id}\n\n")
            f.write(f"Response: {response.status_code}\n")
            f.write(f"Error: {response_error_reason}\n")

    json_response = response.json()
    html = ''
    if 'syllabus_body' in page_url:
        html = json_response.get('syllabus_body')
    else:
        html = json_response.get('body')
    
    if not html:
        print(f"Empty page content: {page_url}")
        return
    soup = BeautifulSoup(html, 'html.parser')

    # Save the HTML content
    save_html(page_url, soup.prettify(), course_name)
    
    # Find and download any files in the page (e.g., <a href="...file">)
    all_links = soup.find_all('a', href=True)
    
    for link in all_links:
        href = link['href']
        full_url = urljoin(page_url, href)
        parsed_full_url = urlparse(full_url)
        print(f'Parsing: {full_url}')
        if not CANVAS_DOMAIN in parsed_full_url.netloc or full_url in visited:
            continue
        go_visit = True

        # Check if the link is a file download (Canvas files often have '/files/' in the URL)
        # TODO: This has been mostly trial and error and needs more research
        if '/files/' in full_url:
            match = file_id_pattern.search(full_url)
            if not match:
                query_params = parse_qs(parsed_full_url.query)
                # Some files have a 'preview' query parameter instead of the file ID
                # TODO: This needs to be written as a better case distinction
                if 'preview' in query_params:
                    file_id = query_params['preview'][0]
                else:
                    raise Exception(f"Failed to parse file ID from URL: {full_url}")
            else:
                file_id = match.group(1)
            # file_id = match.group(1)
            file_info_req_url = f"{BASE_URL}/files/{file_id}"
            #print(f"Fetching file: {file_info_req_url}")
            file_info_res = requests.get(file_info_req_url, headers=headers)
            if file_info_res.status_code != 200:
                print(f"Failed to fetch file: {file_info_req_url}")
                res_content_type = file_info_res.headers.get('Content-Type')
                res_error_reason = ''
                if res_content_type and 'application/json' in res_content_type:
                    res_error_json = file_info_res.json()
                    res_error_reason = json.dumps(res_error_json.get('errors'))
                
                # TODO: I hate this too. Use a logger plz
                # TODO: Also, user should have a choice if they want to interrupt on errors
                with open('error_log.txt', 'a') as f:
                    f.write(f"Failed to fetch file: {file_info_req_url}\n")
                    f.write(f"Response: {file_info_res.status_code}\n")
                    f.write(f"Error: {res_error_reason}\n")
                    f.write(f"Content-Type: {res_content_type}\n")
                    f.write(f"Course: {course_name}\n")
                    f.write(f"Course ID: {course_id}\n")
                    f.write(f"File ID: {file_id}\n")
                    f.write(f"URL: {full_url}\n\n")
                print(f"Failed to fetch file: {file_info_req_url}")
                continue
                # raise Exception(f"Failed to fetch file: {file_info_req_url}")
            file_info_res_json = file_info_res.json()
            file_name = sanitize_filename(file_info_res_json.get('display_name', f'file_{file_id}'))
            file_download_url = file_info_res_json.get('url', '')
            if not file_download_url:
                # TODO: Similarly to the remarks above
                print(f"File download URL not found: {file_info_req_url}")
                with open('error_log.txt', 'a') as f:
                    f.write(f"File download URL not found: {file_info_req_url}\n")
                    f.write(f"Course: {course_name}\n")
                    f.write(f"Course ID: {course_id}\n")
                    f.write(f"File ID: {file_id}\n")
                    f.write(f"URL: {full_url}\n\n")
                continue
            file_save_path = os.path.join('courses', course_name)
            # TODO: Not sure if save_dirs should be handled here
            os.makedirs(file_save_path, exist_ok=True)
            file_save_location = os.path.join(file_save_path, file_name)
            download_file_mod(file_download_url, file_save_location)
            continue
        # TODO: Add module support
        elif '/modules' in full_url:
            continue  # Skip module links for now
        # TODO: Add more edge cases support for pages. Sometimes pages contain other ids on it 
        #       For example it can be /pages/<page_url>#TOC_<page_id>. Both should be supported and crawled
        #       Furthermore, it should be able to tell if pages are similar or not
        elif '/pages/' in full_url:
            page_id = href.split('/')[-1]
            full_url = f"{BASE_URL}/pages/{page_id}"
        else:
            # TODO: Investigate other link types
            print (f"Link type not supported: {full_url}")
            with open('ignored_links.txt', 'a') as f:
                f.write(f"Link type not supported: {full_url}\n")
            time.sleep(1)
            continue

        # Crawl linked Canvas pages (only within the Canvas domain)
        parsed_link = urlparse(full_url)
        if CANVAS_DOMAIN in parsed_link.netloc and full_url not in visited:
            crawl_page(full_url, course_name, course_id, visited)

# Main function to process each course homepage and start crawling
def begin_crawling():
    courses = get_courses()
    if not courses:
        print("No courses found.")
        return

    for course in courses:
        # TODO: Try to guess course name from files
        course_name = course.get('name', 'Unnamed_Course').replace('/', '_')  # Avoid directory issues with slashes
        course_id = course['id']
        print(f"\nProcessing Course: {course_name} (ID: {course_id})")

        # Crawling starts from the course homepage and syllabus
        # Get the course homepage URL
        homepage_url = f'{API_URL}/courses/{course_id}/front_page'
        syballus_url = f'{API_URL}/courses/{course_id}?include[]=syllabus_body'
        
        # Start crawling from the homepage
        visited_links = set()  # To avoid re-crawling the same pages
        crawl_page(homepage_url, course_name, course_id, visited_links)
        crawl_page(syballus_url, course_name, course_id, visited_links)
