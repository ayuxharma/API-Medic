from pathlib import Path

from .state import AgentState


class FileInputParser:
    """
    Convert structured API-error text into AgentState.
    """

    FIELD_LABELS = {
        "endpoint": "endpoint",
        "method": "method",
        "status code": "status_code",
        "error message": "error_message",
        "stack trace": "stack_trace",
    }

    def parse(self, file_path: str | Path) -> AgentState:
        """
        Read a UTF-8 text file from disk and parse its contents.

        This method is used by the command-line application.
        """

        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(
                f"Input file was not found: {path}"
            )

        if not path.is_file():
            raise ValueError(
                f"Input path is not a file: {path}"
            )

        try:
            content = path.read_text(encoding="utf-8")
        except UnicodeDecodeError as error:
            raise ValueError(
                "Input file must contain valid UTF-8 text"
            ) from error

        return self.parse_text(content)
    

    def parse_text(self, content: str) -> AgentState:
        """
        Parse structured text that is already available in memory.

        This method is used by web file uploads.
        """

        if not content.strip():
            raise ValueError("Input content cannot be empty")

        sections: dict[str, list[str]] = {
            "endpoint": [],
            "method": [],
            "status_code": [],
            "error_message": [],
            "stack_trace": [],
        }

        current_field: str | None = None

        for raw_line in content.splitlines():
            stripped_line = raw_line.strip()

            matched_field = self._find_field(stripped_line)

            if matched_field is not None:
                field_name, inline_value = matched_field
                current_field = field_name

                if inline_value:
                    sections[field_name].append(inline_value)

                continue

            if current_field is not None:
                sections[current_field].append(
                    raw_line.rstrip()
                )

        endpoint = self._join_lines(
            sections["endpoint"]
        ) or "Not provided"

        method = (
            self._join_lines(sections["method"]) or "GET"
        ).upper()

        status_code = self._parse_status_code(
            self._join_lines(sections["status_code"])
        )

        error_message = self._join_lines(
            sections["error_message"]
        )

        stack_trace = self._join_lines(
            sections["stack_trace"]
        )

        if not error_message:
            raise ValueError(
                "Error Message is required in the input"
            )

        return {
            "endpoint": endpoint,
            "method": method,
            "status_code": status_code,
            "error_message": error_message,
            "stack_trace": stack_trace,
        }

    def _find_field(
        self,
        line: str,
    ) -> tuple[str, str] | None:
        """
        Check whether a line begins a recognized section.
        """

        if ":" not in line:
            return None

        label, inline_value = line.split(":", maxsplit=1)

        normalized_label = label.strip().lower()
        field_name = self.FIELD_LABELS.get(normalized_label)

        if field_name is None:
            return None

        return field_name, inline_value.strip()

    @staticmethod
    def _join_lines(lines: list[str]) -> str:
        """
        Join multiline section content and remove outside whitespace.
        """
        return "\n".join(lines).strip()

    @staticmethod
    def _parse_status_code(value: str) -> int | None:
        """
        Convert the optional status-code text into an integer.
        """

        if not value:
            return None

        try:
            status_code = int(value)
        except ValueError as error:
            raise ValueError(
                f"Invalid status code: {value}"
            ) from error

        if not 100 <= status_code <= 599:
            raise ValueError(
                "Status code must be between 100 and 599"
            )

        return status_code