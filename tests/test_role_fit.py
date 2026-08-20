from io import BytesIO

from modules.ai_engine import AIEngine
from modules.document_parser import compact_text, extract_uploaded_text


class Upload:
    def __init__(self, name, value):
        self.name = name
        self._value = value

    def getvalue(self):
        return self._value


def test_text_upload_is_extracted_and_compacted():
    upload = Upload("resume.txt", b"Python   and   data analysis\nProject result")
    assert extract_uploaded_text(upload).startswith("Python")
    assert compact_text("a   b\n c") == "a b c"


def test_demo_role_match_returns_practice_questions():
    result = AIEngine.demo_role_match("Built a Python dashboard with Git", "Internship needs Python and SQL")
    assert result["match_score"] > 0
    assert "Python" in result["matched_skills"]
    assert len(result["questions"]) >= 6
