from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime


class CanvasCourse(BaseModel):
    # The unique identifier for the course
    id: int
    # The SIS identifier for the course, if defined
    sis_course_id: Optional[str] = None
    # The UUID of the course
    uuid: str
    # The integration identifier for the course, if defined
    integration_id: Optional[str] = None
    # The unique identifier for the SIS import
    sis_import_id: Optional[int] = None
    # The full name of the course
    name: str
    # The course code
    course_code: str
    # The actual course name
    original_name: Optional[str] = None
    # The current state of the course
    workflow_state: str
    # The account associated with the course
    account_id: int
    # The root account associated with the course
    root_account_id: int
    # The enrollment term associated with the course
    enrollment_term_id: int
    # A list of grading periods associated with the course
    grading_periods: Optional[List[Dict]] = None
    # The grading standard associated with the course
    grading_standard_id: Optional[int] = None
    # The grade passback setting set on the course
    grade_passback_setting: Optional[str] = None
    # The date the course was created
    created_at: Optional[datetime] = None
    # The start date for the course
    start_at: Optional[datetime] = None
    # The end date for the course
    end_at: Optional[datetime] = None
    # The course-set locale
    locale: Optional[str] = None
    # A list of enrollments linking the current user to the course
    enrollments: Optional[List[Dict]] = None
    # The total number of active and invited students in the course
    total_students: Optional[int] = None
    # Course calendar
    calendar: Optional[Dict] = None
    # The type of page that users will see when they first visit the course
    default_view: str
    # User-generated HTML for the course syllabus
    syllabus_body: Optional[str] = None
    # The number of submissions needing grading
    needs_grading_count: Optional[int] = None
    # The enrollment term object for the course
    term: Optional[Dict] = None
    # Information on progress through the course
    course_progress: Optional[Dict] = None
    # Weight final grade based on assignment group percentages
    apply_assignment_group_weights: bool
    # The permissions the user has for the course
    permissions: Optional[Dict[str, bool]] = None
    # Is the course public
    is_public: bool
    # Is the course public to authenticated users
    is_public_to_auth_users: bool
    # Is the syllabus public
    public_syllabus: bool
    # Is the syllabus public to authenticated users
    public_syllabus_to_auth: bool
    # The public description of the course
    public_description: Optional[str] = None
    # Storage quota in MB
    storage_quota_mb: Optional[int] = None
    # Storage quota used in MB
    storage_quota_used_mb: Optional[int] = None
    # Hide final grades
    hide_final_grades: bool
    # License type
    license: Optional[str] = None
    # Allow student assignment edits
    allow_student_assignment_edits: Optional[bool] = None
    # Allow wiki comments
    allow_wiki_comments: Optional[bool] = None
    # Allow student forum attachments
    allow_student_forum_attachments: Optional[bool] = None
    # Open enrollment
    open_enrollment: Optional[bool] = None
    # Self enrollment
    self_enrollment: Optional[bool] = None
    # Restrict enrollments to course dates
    restrict_enrollments_to_course_dates: bool
    # Course format (e.g., 'online')
    course_format: Optional[str] = None
    # Whether access is restricted by date
    access_restricted_by_date: Optional[bool] = None
    # Course time zone
    time_zone: Optional[str] = None
    # Whether the course is a blueprint
    blueprint: Optional[bool] = None
    # Blueprint restrictions
    blueprint_restrictions: Optional[Dict[str, bool]] = None
    # Blueprint restrictions by object type
    blueprint_restrictions_by_object_type: Optional[Dict[str, Dict[str, bool]]] = None
    # Whether the course is a template
    template: Optional[bool] = None

    class Config:
        orm_mode = True
        use_enum_values = True


class CanvasPage(BaseModel):
    # The ID of the page
    page_id: int
    # The unique locator for the page (slug)
    url: str
    # The title of the page
    title: str
    # The creation date for the page
    created_at: datetime
    # The date the page was last updated
    updated_at: datetime
    # Whether this page is hidden from students (deprecated)
    hide_from_students: bool
    # Roles allowed to edit the page; comma-separated list
    editing_roles: str
    # The User who last edited the page (optional, can be None)
    last_edited_by: Optional[Dict] = None
    # The page content, in HTML
    body: str
    # Whether the page is published or in draft state
    published: bool
    # Scheduled publication date for this page
    publish_at: Optional[datetime] = None
    # Whether this page is the front page for the wiki
    front_page: bool
    # Whether or not this is locked for the user
    locked_for_user: bool
    # Information for the user about the lock (present when locked_for_user is True)
    lock_info: Optional[str] = None
    # An explanation of why this is locked for the user (present when locked_for_user is True)
    lock_explanation: Optional[str] = None

    class Config:
        orm_mode = True
