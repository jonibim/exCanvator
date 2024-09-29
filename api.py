import logging
from re import T
from typing import Generic, Optional, TypeVar, Type
from pydantic import BaseModel, ValidationError
import requests
from endpoints import (
    COURSE_ASSIGNMENTS_ENDPOINT,
    COURSE_FRONTPAGE_ENDPOINT,
    COURSE_PAGE_ENDPOINT,
    COURSE_SUBMISSION_ENDPOINT,
    COURSES_ENDPOINT,
    COURSE_FILES_ENDPOINT,
    COURSE_MODULES_ENDPOINT,
    COURSE_MODULES_ITEMS_ENDPOINT,
)
from models import CanvasCourse, CanvasPage

T = TypeVar("T", bound=BaseModel)


class CanvasAPIResponse(Generic[T]):
    def __init__(
        self, status_code: int, content: Optional[str] = None, data: Optional[T] = None
    ):
        self.status_code = status_code
        self.content = content
        self.data = data

    def __repr__(self):
        return f"APIResponse(status_code={self.status_code}, content={self.content}, data={self.data})"


# TODO: Write documentation and return types
class CanvasAPIClient:
    def __init__(self, access_token, domain_url, logger=None):
        self.access_token = access_token
        self.domain_url = domain_url
        self.api_url = f"https://{domain_url}/api/v1"

        self.auth_headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
            "Charset": "UTF-8",
        }

        self.logger = logger or logging.getLogger(__name__)
        self.logger.debug(f"Initialized Canvas API client for {domain_url}")

    def _handle_response(
        self, response: requests.Response, model: Type[T]
    ) -> CanvasAPIResponse[T]:
        try:
            response.raise_for_status()
            data = model.model_validate_json(response.text)
            self.logger.debug(f"Successful fetch for {model}")
            return CanvasAPIResponse(status_code=response.status_code, data=data)
        except ValidationError as e:
            self.logger.error(f"Validation error: {e}")
            self.logger.error(f"Response content: {response.content}")
            return CanvasAPIResponse(status_code=response.status_code)
        except requests.HTTPError as e:
            self.logger.error(f"HTTP error: {e}")
            return CanvasAPIResponse(status_code=response.status_code)

    # Function to get the front page of a course
    def get_course_frontpage(self, course_id: int) -> CanvasAPIResponse[CanvasPage]:
        # Reference: https://canvas.instructure.com/doc/api/pages.html#method.wiki_pages_api.show_front_page
        endpoint = (
            f"{self.api_url}{COURSE_FRONTPAGE_ENDPOINT.format(course_id=course_id)}"
        )
        self.logger.debug(f"Fetching front page in {endpoint}")
        return self._handle_response(
            requests.get(endpoint, headers=self.auth_headers), CanvasPage
        )

    # Function to get a page of a course
    def get_course_page(
        self, course_id: int, page_id: int
    ) -> CanvasAPIResponse[CanvasPage]:
        # Reference: https://canvas.instructure.com/doc/api/pages.html#method.wiki_pages_api.show_front_page
        endpoint = f"{self.api_url}{COURSE_PAGE_ENDPOINT.format(course_id=course_id, page_id=page_id)}"
        self.logger.debug(f"Fetching front page in {endpoint}")
        return self._handle_response(
            requests.get(endpoint, headers=self.auth_headers), CanvasPage
        )

    # Function to get the syllabus page of a course
    def get_course(
        self, course_id: int, with_syllabus: bool = False
    ) -> CanvasAPIResponse[CanvasCourse]:
        # Reference: https://canvas.instructure.com/doc/api/courses.html#method.courses.show
        endpoint = f"{self.api_url}{COURSES_ENDPOINT.format(course_id=course_id)}"
        self.logger.debug(f"Fetching syllabus for course {course_id} in {endpoint}")

        # TODO: Maybe just pass the params individually
        params = {"include": "syllabus_body"} if with_syllabus else {}

        return self._handle_response(
            requests.get(endpoint, headers=self.auth_headers, params=params),
            CanvasCourse,
        )

    # Function to get all courses
    def get_courses(self) -> list[str]:
        # Reference: https://canvas.instructure.com/doc/api/courses.html
        endpoint = f'{self.api_url}{COURSES_ENDPOINT.format(course_id="")}'
        self.logger.debug(f"Fetching all courses in {endpoint}")
        courses = []
        page = 1

        # TODO: Maybe use the LINK header to get the next page
        while True:

            response = requests.get(
                endpoint, headers=self.auth_headers, params={"page": page}
            )

            if response.status_code != 200:
                # TODO: Also return the error code
                self.logger.error(
                    f"Failed to fetch all courses: {response.status_code} -> {response.content}"
                )
                return courses

            # TODO: Create respective types for the returned data
            data = response.json()
            if not data:
                break

            self.logger.debug(f"Successful fetch {len(data)} courses from page {page}")
            courses.extend(data)
            page += 1

        self.logger.debug(f"Fetched {len(courses)} courses in {page} pages")
        return courses

    # Function to get all files in a course
    def get_course_files(self, course_id: int, file_id: Optional[int] = None) -> list:
        # Reference: https://canvas.instructure.com/doc/api/files.html
        endpoint = f"{self.api_url}{COURSE_FILES_ENDPOINT.format(course_id=course_id, file_id=file_id)}"
        self.logger.debug(f"Fetching all files from course {course_id} in {endpoint}")

        files = []
        page = 1

        while True:
            response = requests.get(
                endpoint, headers=self.auth_headers, params={"page": page}
            )
            if response.status_code != 200:
                # TODO: Also return the error code
                self.logger.error(
                    f"Failed to fetch files for course {course_id}: {response.status_code} -> {response.content}"
                )
                return files

            # TODO: Create respective types for the returned data
            data = response.json()
            if not data:
                break

            self.logger.debug(
                f"Successful fetch {len(data)} files from course {course_id} at page {page}"
            )

            # If a file_id is provided, we only need to fetch that file
            if file_id:
                files.append(data)
                break

            if file_id:
                break
            page += 1

        self.logger.debug(
            f"Fetched {len(files)} files from course {course_id} in {page} pages"
        )
        return files

    # Function to get all assignments in a course
    def get_course_assignments(
        self, course_id: int, assignment_id: Optional[int] = None
    ):
        # Reference: https://canvas.instructure.com/doc/api/assignments.html
        endpoint = f"{self.api_url}{COURSE_ASSIGNMENTS_ENDPOINT.format(course_id=course_id, assignment_id=assignment_id)}"
        self.logger.debug(
            f"Fetching all assignments from course {course_id} in {endpoint}"
        )

        assignments = []
        page = 1

        while True:
            response = requests.get(
                endpoint, headers=self.auth_headers, params={"page": page}
            )
            if response.status_code != 200:
                # TODO: Also return the error code
                self.logger.error(
                    f"Failed to fetch assignments for course {course_id}: {response.status_code} -> {response.content}"
                )
                return assignments

            # TODO: Create respective types for the returned data
            data = response.json()
            if not data:
                break

            self.logger.debug(
                f"Successful fetch {len(data)} assignments from course {course_id} at page {page}"
            )
            if assignment_id:
                assignments.append(data)
                break

            assignments.extend(data)
            page += 1

        self.logger.debug(
            f"Fetched {len(assignments)} assignments from {course_id} in {page} pages"
        )
        return assignments

    # Function to get all modules in a course
    def get_modules(self, course_id: int, module_id: Optional[int] = None):
        # Reference: https://canvas.instructure.com/doc/api/modules.html
        endpoint = f"{self.api_url}{COURSE_MODULES_ENDPOINT.format(course_id=course_id, module_id=module_id)}"
        self.logger.debug(f"Fetching all modules from course {course_id} in {endpoint}")

        modules = []
        page = 1

        while True:
            response = requests.get(
                endpoint, headers=self.auth_headers, params={"page": page}
            )
            if response.status_code != 200:
                # TODO: Also return the error code
                self.logger.error(
                    f"Failed to fetch modules for course {course_id}: {response.status_code} -> {response.content}"
                )
                return modules

            # TODO: Create respective types for the returned data
            data = response.json()
            if not data:
                break  # No more modules

            self.logger.debug(
                f"Successful fetch {len(data)} modules from course {course_id} at page {page}"
            )
            if module_id:
                modules.append(data)
                break

            page += 1
            modules.extend(data)

        self.logger.debug(
            f"Fetched {len(data)} modules from course {course_id} in {page} pages"
        )
        return modules

    # TODO: Add verbose logging and error handling
    # Function to get items in a module
    def get_module_items(
        self, course_id: int, module_id: int, item_id: Optional[int] = None
    ):
        # Reference: https://canvas.instructure.com/doc/api/modules.html#method.context_module_items_api.index
        endpoint = f"{self.api_url}{COURSE_MODULES_ITEMS_ENDPOINT.format(course_id=course_id, module_id=module_id, item_id=item_id)}"
        self.logger.debug(f"Fetching items for module {module_id} in {endpoint}")

        items = []
        page = 1

        while True:
            response = requests.get(
                endpoint, headers=self.auth_headers, params={"page": page}
            )
            if response.status_code != 200:
                # TODO: Also return the error code
                self.logger.error(
                    f"Failed to fetch items for module {module_id}: {response.status_code} -> {response.content}"
                )
                return items

            # TODO: Create respective types for the returned data
            data = response.json()
            if not data:
                break  # No more items

            self.logger.debug(
                f"Successful fetch {len(data)} module items from course {course_id} at page {page}"
            )
            if item_id:
                items.append(data)
                break

            items.extend(data)
            page += 1

        self.logger.debug(
            f"Fetched {len(data)} module items from course {course_id} in {page} pages"
        )
        return items

    # TODO: This needs to be investigated further
    # Function to get submission details for an assignment
    def get_course_self_assignment_submission(self, course_id: int, assignment_id: int):
        # Reference: https://canvas.instructure.com/doc/api/submissions.html
        endpoint = f"{self.api_url}{COURSE_SUBMISSION_ENDPOINT.format(course_id=course_id, assignment_id=assignment_id)}/self"
        self.logger.debug(
            f"Fetching self submission for assignment {assignment_id} in {endpoint}"
        )

        response = requests.get(endpoint, headers=self.auth_headers)

        if response.status_code != 200:
            # TODO: Also return the error code
            self.logger.debug(
                f"Failed to fetch submission for assignment {assignment_id}: {response.status_code} -> {response.content}"
            )
            return None

        self.logger.debug(f"Successful fetch submission for assignment {assignment_id}")
        # TODO: Should return a Submission type + return code
        return response.json()
