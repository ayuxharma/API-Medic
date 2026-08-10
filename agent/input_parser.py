from pathlib import Path
from .state import AgentState

class FileInputParser :
    """ reads api failure details from a structured text file."""
    
    def parse(self, file_path : str) -> AgentState :
        "read a file and convert its content into agentstate"
        
        path = Path(file_path)
        
        if not path.exists() :
            raise FileNotFoundError(f"Input file does not exist: {file_path}")
        
        if not path.is_file() :
            raise ValueError(f"Input path is not a file: {file_path}")
        
        content = path.read_text(encoding="utf-8")
        lines = content.splitlines()
        
        state : AgentState = {
            "endpoint" : "Not Provided" ,
            "method" : "GET" ,
            "status_code" : None ,
            "error_message" : "" ,
            "stack_trace" : "" ,
        }
        
        sections = {
            "error_message" : [] ,
            "stack_trace" : [] ,
        }
        
        current_section = None
        
        for line in lines :
            stripped_line = line.strip()
            
            if stripped_line.startswith("Endpoint:") :
                state["endpoint"] = stripped_line.split(
                    ":" ,
                    1 ,
                )[1].strip()
                
                current_section = None
                continue 
            
            if stripped_line.startswith("Method:"):
                method = stripped_line.split(":", 1)[1].strip()

                state["method"] = method.upper() or "GET"
                current_section = None
                continue

            if stripped_line.startswith("Status Code:"):
                status_text = stripped_line.split(
                    ":",
                    1,
                )[1].strip()

                if not status_text:
                    state["status_code"] = None
                else:
                    try:
                        state["status_code"] = int(status_text)
                    except ValueError as error:
                        raise ValueError(
                            f"Invalid status code: {status_text}"
                        ) from error

                current_section = None
                continue

            if stripped_line.startswith("Error Message:"):
                current_section = "error_message"

                inline_value = stripped_line.split(
                    ":",
                    1,
                )[1].strip()

                if inline_value:
                    sections["error_message"].append(
                        inline_value
                    )

                continue

            if stripped_line.startswith("Stack Trace:"):
                current_section = "stack_trace"

                inline_value = stripped_line.split(
                    ":",
                    1,
                )[1].strip()

                if inline_value:
                    sections["stack_trace"].append(
                        inline_value
                    )

                continue

            if current_section is not None:
                sections[current_section].append(
                    line.rstrip()
                )
                
        state["error_message"] = "\n".join(
            sections["error_message"]
        ).strip()

        state["stack_trace"] = "\n".join(
            sections["stack_trace"]
        ).strip()

        if not state["error_message"]:
            raise ValueError(
                "Input file must contain an Error Message"
            )

        return state