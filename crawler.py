from enum import Enum
import logging
import os
import re
from typing import Optional
from bs4 import BeautifulSoup
from logger import ignore_logger

from urllib.parse import ParseResult, parse_qs, urljoin, urlparse
from api import CanvasAPIClient
from functions import download_file, sanitize_filename, save_html

# Regular expressions to extract file IDs and preview IDs from Canvas URLs
# TODO: More patterns should be added and tested
file_id_pattern = re.compile(r"/files/(\d+)")
preview_id_pattern = re.compile(r"preview=(\d+)")


class SupportedURLCrawl(Enum):
    PAGES = "/pages"
    HOME = "/front_page"
    SYLLABUS = "include[]=syllabus_body"
    NONE = ""


class CanvasCrawler:
    def __init__(self, client, logger=None):
        self.client: CanvasAPIClient = client
        self.logger = logger or logging.getLogger(__name__)

    def _check_supported_link(self, url_form: ParseResult) -> SupportedURLCrawl:
        if not url_form.netloc or url_form.netloc != self.client.domain_url:
            self.logger.debug(f"URL domain not same as the client: {url_form.netloc}")
            return SupportedURLCrawl.NONE

        if not url_form.path:
            self.logger.debug(f"URL path not provided")
            return SupportedURLCrawl.NONE

        if SupportedURLCrawl.PAGES.value in url_form.path:
            return SupportedURLCrawl.PAGES
        elif SupportedURLCrawl.HOME.value in url_form.path:
            return SupportedURLCrawl.HOME
        elif SupportedURLCrawl.SYLLABUS.value in url_form.query:
            return SupportedURLCrawl.SYLLABUS
        else:
            self.logger.debug(f"URL path not supported: {url_form.path}")
            return SupportedURLCrawl.NONE

    def _extract_course_id(self, url: str) -> Optional[int]:
        pattern = re.compile(r"/courses/(\d+)")
        match = pattern.search(url)
        if match:
            return int(match.group(1))
        raise None

    def _extract_page_identifier(self, url: str) -> Optional[str]:
        pattern = re.compile(r"/courses/\d+/pages/([^/#?]+)")
        match = pattern.search(url)
        if match:
            return match.group(1)
        return None

    # Function to crawl and download files/pages recursively
    def crawl_page(self, page_url: str, visited: Optional[list[str]] = None):

        if visited is None:
            visited = set()

        # Check if the page has already been visited
        if page_url in visited:
            self.logger.debug(f"Page already visited: {page_url}")
            return

        try:
            url_form = urlparse(page_url)
        except Exception as e:
            self.logger.error(f"Failed to parse URL: {page_url}")
            raise Exception(f"Failed to parse URL: {page_url}, Details: {e}")

        visited.add(page_url)
        self.logger.debug(f"Visiting: {page_url}")

        link_type = self._check_supported_link(url_form)

        if link_type == SupportedURLCrawl.NONE:
            self.logger.debug(f"Skipping unsupported link: {page_url}")
            ignore_logger.error(f"{page_url}: Unsupported link")
            return

        page_id = None
        course_id = self._extract_course_id(page_url)
        if course_id is None:
            self.logger.error(f"Failed to extract course ID from URL: {page_url}")
            ignore_logger.error(f"{page_url}: Failed to extract course ID")
            # raise Exception(f"Failed to extract course ID from URL: {page_url}")
        self.logger.debug(f"Fetching course info from: {page_url}")
        response_info = self.client.get_course(course_id, with_syllabus=True)
        if response_info.status_code != 200:
            self.logger.error(f"Failed to fetch course info: {page_url}")
            ignore_logger.error(f"{page_url}: Failed to fetch course info")
            return
        course_name = response_info.data.name or f"Unknown_Course_{course_id}"
        html_body = response_info.data.syllabus_body

        if link_type != SupportedURLCrawl.SYLLABUS:
            if link_type == SupportedURLCrawl.HOME:
                response = self.client.get_course_frontpage(course_id)
                if response.status_code != 200:
                    self.logger.error(f"Failed to fetch front page: {page_url}")
                    ignore_logger.error(f"{page_url}: Failed to fetch front page")
                    return
                html_body = response.data.body
            else:
                page_id = self._extract_page_identifier(page_url)
                if page_id is None:
                    self.logger.error(f"Failed to extract page ID from URL: {page_url}")
                    raise Exception(f"Failed to extract page ID from URL: {page_url}")
                self.logger.debug(f"Fetching page: {page_url}")
                self.logger.debug(f"Got page ID: {page_id}")
                response = self.client.get_course_page(course_id, page_id)
                if response.status_code != 200:
                    self.logger.error(f"Failed to fetch page: {page_url}")
                    ignore_logger.error(f"{page_url}: Failed to fetch page")
                    return
                html_body = response.data.body

        if not html_body:
            self.logger.warning(f"Empty page content: {page_url}")
            ignore_logger.error(f"{page_url}: Empty page content")
            return

        # Save the HTML content
        soup = BeautifulSoup(html_body, "html.parser")
        save_html(page_url, soup.prettify(), course_name)

        # Find and download any files in the page (e.g., <a href="...file">)
        all_links = soup.find_all("a", href=True)

        course_base_url = f"{self.client.api_url}/courses/{course_id}"
        for link in all_links:
            href = link["href"]
            full_url = urljoin(page_url, href)
            parsed_full_url = urlparse(full_url)
            self.logger.info(f"Parsing: {full_url}")
            if (
                not self.client.domain_url in parsed_full_url.netloc
                or full_url in visited
            ):
                continue
            go_visit = True

            # Check if the link is a file download (Canvas files often have '/files/' in the URL)
            # TODO: This has been mostly trial and error and needs more research

            # IMPORTANT: The urls in this section need to be converted to API calls
            if "/files/" in full_url:
                match = file_id_pattern.search(full_url)
                if not match:
                    query_params = parse_qs(parsed_full_url.query)
                    # Some files have a 'preview' query parameter instead of the file ID
                    # TODO: This needs to be written as a better case distinction
                    if "preview" in query_params:
                        file_id = query_params["preview"][0]
                    else:
                        self.logger.error(
                            f"Failed to parse file ID from URL: {full_url}"
                        )
                        ignore_logger.error(f"{full_url}: Failed to parse file ID")
                        continue
                        # raise Exception(f"Failed to parse file ID from URL: {full_url}")
                else:
                    file_id = match.group(1)
                file_info_req_url = f"{course_base_url}/files/{file_id}"
                self.logger.debug(f"Fetching file: {file_info_req_url}")
                file_info_res = self.client.get_course_files(course_id, file_id)
                if len(file_info_res) == 0:
                    self.logger.error(f"Failed to fetch file info: {file_info_req_url}")
                    ignore_logger.error(
                        f"{file_info_req_url}: Failed to fetch file info"
                    )
                    continue
                file_info_res_json = file_info_res[0]
                file_name = sanitize_filename(
                    file_info_res_json.get("display_name", f"file_{file_id}")
                )
                file_download_url = file_info_res_json.get("url", "")
                if not file_download_url:
                    self.logger.error(
                        f"File download URL not found: {file_info_req_url}; {file_info_res_json}; {full_url}"
                    )
                    ignore_logger.error(
                        f"{file_info_req_url}: File download URL not found"
                    )
                    continue
                file_save_path = os.path.join("courses", course_name, "cv_files")
                # TODO: Not sure if save_dirs should be handled here
                os.makedirs(file_save_path, exist_ok=True)
                file_save_location = os.path.join(file_save_path, file_name)
                file_info = (file_download_url, file_save_location)
                download_file(file_info, self.client.access_token)
                continue
            # TODO: Add module support
            # TODO: Add more edge cases support for pages. Sometimes pages contain other ids on it
            #       For example it can be /pages/<page_url>#TOC_<page_id>. Both should be supported and crawled
            #       Furthermore, it should be able to tell if pages are similar or not
            elif "/pages" in full_url:
                self.logger.debug(f"Found page: {full_url}")
                self.crawl_page(full_url, visited)
                # page_id = href.split("/")[-1]
                # full_url = f"{BASE_URL}/pages/{page_id}"
            else:
                # TODO: Investigate other link types
                self.logger.warning(f"Link type not supported: {full_url}")
                ignore_logger.error(f"{full_url}: Link type not supported")
