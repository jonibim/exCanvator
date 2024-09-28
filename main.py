import requests
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
import json

from functions import API_URL, begin_crawling, headers, download_file, get_assignments, get_courses, get_files, get_module_items, get_modules, get_page_content, get_submission, save_assignment_description, save_grade_and_comments, save_page_content


download = False

#TODO: Obviously this also needs to be refactored and functions need to be merged
#TODO: Preferably add test files

# Main function to download assignment details, submissions, and save results
def download_assignments_and_submissions(workers):
    courses = get_courses()
    if not courses:
        print("No courses found.")
        return

    for course in courses:
        course_name = course.get('name', 'Unnamed_Course').replace('/', '_')  # Avoid directory issues with slashes
        course_id = course['id']
        print(f"\nCourse: {course_name} (ID: {course_id})")

        # Get all assignments for the course
        assignments = get_assignments(course_id)
        if not assignments:
            print(f"No assignments found for course: {course_name}")
            continue

        file_downloads = []  # List to hold all file download tasks

        for assignment in assignments:
            assignment_name = assignment.get('name', 'Unnamed_Assignment').replace('/', '_')
            assignment_id = assignment['id']
            print(f"  Assignment: {assignment_name} (ID: {assignment_id})")

            # Create directory structure for the assignment
            course_dir = os.path.join('courses', course_name, 'cv_assignments', assignment_name)
            os.makedirs(course_dir, exist_ok=True)

            # Save assignment description if available
            description = assignment.get('description', None)
            description_file_path = os.path.join(course_dir, 'assignment_description.txt')
            save_assignment_description(description_file_path, description)

            # Download any attached files in the assignment description
            if 'attachments' in assignment and assignment['attachments']:
                for attachment in assignment['attachments']:
                    file_name = attachment['display_name'].replace('/', '_')
                    file_url = attachment['url']
                    save_path = os.path.join(course_dir, file_name)
                    file_downloads.append((file_url, save_path))

            # Fetch submission details
            submission = get_submission(course_id, assignment_id)
            if submission:
                # Download any files attached to the submission
                if 'attachments' in submission and submission['attachments']:
                    for attachment in submission['attachments']:
                        file_name = attachment['display_name'].replace('/', '_')
                        file_url = attachment['url']
                        save_path = os.path.join(course_dir, f'submission_{file_name}')
                        file_downloads.append((file_url, save_path))

                # Save grade and comments to a text file
                result_file_path = os.path.join(course_dir, 'assignment_result_score.txt')
                save_grade_and_comments(result_file_path, submission)
            else:
                print(f"    No submission found for assignment: {assignment_name}")

        # Parallel downloading of files
        if file_downloads:
            with ThreadPoolExecutor(max_workers=workers) as executor:
                futures = [executor.submit(download_file, file_info) for file_info in file_downloads]

                # Wait for all futures to complete
                for future in as_completed(futures):
                    future.result()  # This will raise an exception if any download failed
        else:
            print(f"  No files to download for course: {course_name}")


# Main function to download all files for each course
def download_all_files(workers):
    global download
    courses = get_courses()
    if not courses:
        print("No courses found.")
        return

    for course in courses:
        course_name = course.get('name', 'Unnamed_Course').replace('/', '_')  # Avoid directory issues with slashes
        course_id = course['id']
        print(f"\nCourse: {course_name} (ID: {course_id})")

        if (course_name == "2IOA0 (2019-4) DBL HTI + Webtech"):
            print("continue")
            download = True
            continue
        elif not download:
            print('Skipping')
            continue

        # Get all files for the course
        files = get_files(course_id)
        if files:
            print(f"Found {len(files)} files for course: {course_name}")

            # Create a directory only if there are files
            course_dir = os.path.join('courses', course_name)
            os.makedirs(course_dir, exist_ok=True)

            # Prepare file info for parallel downloading
            file_downloads = [(file['url'], os.path.join(course_dir, file['display_name'].replace('/', '_')))
                              for file in files]

            # Use ThreadPoolExecutor to download files in parallel
            with ThreadPoolExecutor(max_workers=workers) as executor:
                futures = [executor.submit(download_file, file_info) for file_info in file_downloads]

                # Wait for all futures to complete
                for future in as_completed(futures):
                    future.result()  # This will raise an exception if any download failed
        else:
            print(f"No files found for course: {course_name}")


# Main function to download files from modules in all courses
def download_files_from_modules(workers):
    global download
    courses = get_courses()
    if not courses:
        print("No courses found.")
        return

    for course in courses:
        course_name = course.get('name', 'Unnamed_Course').replace('/', '_')  # Avoid directory issues
        course_id = course['id']
        print(f"\nCourse: {course_name} (ID: {course_id})")

        # if (course_name == "2IC80 (2020-4) Lab on offensive computer security"):
        #     print("continue")
        #     download = True
        #     continue
        # elif not download:
        #     print('Skipping')
        #     continue


        # Get all modules for the course
        modules = get_modules(course_id)
        if not modules:
            print(f"No modules found for course: {course_name}")
            continue

        # List to hold all files that need to be downloaded
        file_downloads = []
        external_links = []

        for module in modules:
            module_name = module.get('name', 'Unnamed_Module').replace('/', '_')
            module_id = module['id']
            print(f"  Module: {module_name} (ID: {module_id})")

            # Get all items in the module
            module_items = get_module_items(course_id, module_id)
            if not module_items:
                print(f"    No items found in module: {module_name}")
                continue

            for item in module_items:
                # Check the type of item
                item_type = item['type']
                if item_type == 'File':
                    # Handle file attachments
                    file_name = item['title'].replace('/', '_')
                    file_url = f'{API_URL}/courses/{course_id}/files/{item["content_id"]}'
                    file_response = requests.get(file_url, headers=headers)
                    file_obj = file_response.json()
                    # Prepare the download directory for the course and module
                    course_dir = os.path.join('courses', course_name, 'cv_modules', module_name)
                    os.makedirs(course_dir, exist_ok=True)

                    url = file_obj['url']
                    if url == "":
                        print(f"Can't download {file_obj['display_name']}")
                        no_download_links_path = os.path.join('courses', course_name, 'cv_modules', 'cant_download.txt')
                        with open(no_download_links_path, 'w') as f:
                            f.write(json.dumps(file_obj) + '\n')
                    else:
                        save_path = os.path.join(course_dir, file_name)
                        file_downloads.append((url, save_path))

                elif item_type == 'ExternalUrl':
                    # Save external links
                    external_link = item['external_url']
                    external_links.append(external_link)

                elif item_type == 'Page':
                    # Handle Canvas pages
                    page_url = item['url']  # Use the page URL provided in the item
                    page_title = item['title'].replace('/', '_')
                    page_content = get_page_content(page_url)

                    # Prepare the page save path
                    course_dir = os.path.join('courses', course_name, 'cv_modules', module_name)
                    os.makedirs(course_dir, exist_ok=True)

                    save_path = os.path.join(course_dir, f"{page_title}.txt")
                    save_page_content(page_content, save_path)

        # Download files in parallel
        if file_downloads:
            print(f"Downloading {len(file_downloads)} files")
            with ThreadPoolExecutor(max_workers=min(workers,len(file_downloads))) as executor:
                futures = [executor.submit(download_file, file_info) for file_info in file_downloads]

                # Wait for all futures to complete
                for future in as_completed(futures):
                    future.result()  # This will raise an exception if any download failed
        else:
            print(f"  No files to download in modules for course: {course_name}")

        # Save external links to a file
        if external_links:
            external_links_path = os.path.join('courses', course_name, 'external_links.txt')
            with open(external_links_path, 'w') as f:
                for link in external_links:
                    f.write(link + '\n')
            print(f"Saved external links to: {external_links_path}")

# You have to uncomment and comment for the functions to run
# TODO: User-friendly command line interface with arguments
# TODO: Merge functionality together per course, i.e look for modules, files and assignments in one go for one course
# TODO: MAYBE add parallel downloading for crawling
if __name__ == "__main__":
    # You can change this to any number of workers (threads)
    x = 10  # Specify the number of parallel downloads (workers)
    download_files_from_modules(x)
    download_all_files(x)
    download_assignments_and_submissions(x)
    begin_crawling() # Crawling does not have support for parallel downloads