from .state import AgentState
    
class FailureClassifier:
    """
    Reads API error details and assigns one broad failure category.
    """

    RULES = {
        "AUTHENTICATION": [
            "jwt",
            "token expired",
            "unauthorized",
            "authentication failed",
        ],
        "AUTHORIZATION" : [
            "forbidden" ,
            "permission denied" ,
            "insufficient permission" ,
            "insufficient scope" ,
            "access denied" ,
            "role required" ,
            "not allowed" ,
        ] ,
        "VALIDATION": [
            "required field",
            "is required",
            "missing field",
            "validation error",
        ],
        "SERVER_ERROR": [
            "traceback",
            "undefined",
            "nullpointer",
            "internal server error",
        ],
        "DATABASE" : [
            "database" ,
            "postgres" ,
            "postgresql" ,
            "mysql" ,
            "sqlalchemy" ,
            "psycopg" ,
            "duplicate key" ,
            "unique constraint" ,
            "unique key" ,
            "sql syntax" ,
            "query failed" ,
            "integrityerror" ,
        ] ,
    }
    
    DATABASE_STRONG_SIGNALS = [
    "database connection",
    "psycopg",
    "sqlalchemy.exc",
    "mysql.connector",
    "duplicate key",
    "unique constraint",
    "foreign key constraint",
    "sql syntax",
    "integrityerror",
    ]   

    def classify(self, state: AgentState) -> AgentState:
        # Read input safely. `or ""` prevents problems if a value is missing.
        error_message = (state.get("error_message") or "").lower()
        stack_trace = (state.get("stack_trace") or "").lower()
        status_code = state.get("status_code")

        # Search both the short error and the technical stack trace.
        text_to_check = f"{error_message} {stack_trace}"

        # A score decides which category has the strongest evidence.
        scores = {
            "AUTHENTICATION": 0,
            "AUTHORIZATION" : 0,
            "VALIDATION": 0,
            "SERVER_ERROR": 0,
            "DATABASE" : 0,
        }

        signals : list[str] = []

        # Status codes are stronger evidence than ordinary keywords.
        if status_code == 401:
            scores["AUTHENTICATION"] += 5
            signals.append("HTTP 401 usually means authentication failed")

        elif status_code == 403:
            scores["AUTHORIZATION"] += 5
            signals.append(
                "HTTP 403 usually means access is forbidden"
            )
        
        elif status_code == 400:
            scores["VALIDATION"] += 5
            signals.append("HTTP 400 usually means invalid request data")

        elif status_code is not None and status_code >= 500:
            scores["SERVER_ERROR"] += 5
            signals.append(f"HTTP {status_code} indicates a server-side failure")

        for database_signal in self.DATABASE_STRONG_SIGNALS:
            if database_signal in text_to_check:
                scores["DATABASE"] += 6
                signals.append(
                    f"Matched strong database signal "
                    f"'{database_signal}'"
                )
                break
        
        # Check category-specific words and phrases.
        for category, keywords in self.RULES.items():
            for keyword in keywords:
                if keyword in text_to_check:
                    scores[category] += 1
                    signals.append(f"Matched '{keyword}' for {category}")

        # Find the category with the highest score.
        best_category = max(scores, key=scores.get)

        # If nothing matched, be honest instead of guessing.
        if scores[best_category] == 0:
            state["failure_type"] = "UNKNOWN"
            signals.append("No known classification signal was found")
        else:
            state["failure_type"] = best_category

        state["signals"] = signals
        return state