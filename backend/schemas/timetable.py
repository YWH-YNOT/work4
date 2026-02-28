from pydantic import BaseModel

class TimetableImportResponse(BaseModel):
    message: str
    courses_imported: int
    timetable_entries_created: int
