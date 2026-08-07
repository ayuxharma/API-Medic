from typing import List
from .state import AgentState

class FixSuggester :
    """
    Generates practical debugging steps for the chosen root cause.
    """

    CAUSE_FIXES = {
        "JWT token has expired": [
            "Generate a new authentication token.",
            "Check the JWT exp claim to confirm its expiry time.",
            "Ensure the client refreshes expired tokens before retrying.",
        ],
        "Authorization header is missing or malformed": [
            "Send an Authorization header with the request.",
            "Use the format: Bearer <token>.",
            "Check whether a proxy or frontend is removing the header.",
        ],
        "Token signature verification failed": [
            "Check that token signing and verification use the same secret or public key.",
            "Confirm the JWT algorithm matches the expected algorithm.",
            "Verify that the token was not changed or corrupted in transit.",
        ],
        "Required field is missing from request": [
            "Add the required field to the request body.",
            "Compare the request body with the API documentation or schema.",
            "Check spelling and capitalization of field names.",
        ],
        "Field type mismatch": [
            "Check the expected data type in the API schema.",
            "Convert the submitted value to the required type.",
            "Verify that numbers, booleans, and strings are not sent in the wrong format.",
        ],
        "Field format validation failed": [
            "Check the required format for the field.",
            "Validate values such as email, URL, date, or UUID before sending.",
            "Compare the submitted value with the API schema.",
        ],
        "Null pointer dereference": [
            "Find the variable that is null before it is used.",
            "Add a null check or initialize the missing value.",
            "Inspect the stack trace to locate the failing code line.",
        ],
        "Undefined variable or method call": [
            "Check the spelling of the variable or method name.",
            "Make sure the variable is created before it is used.",
            "Inspect imports and object properties at the failing line.",
        ],
        "Unhandled exception in application code": [
            "Inspect the full stack trace to locate the failing line.",
            "Handle the expected exception near the risky operation.",
            "Add validation and logging around the failure point.",
        ],
    }

    
    CATEGORY_FIXES = {
        "AUTHENTICATION": [
            "Check the Authorization header and token lifecycle.",
            "Verify authentication configuration and credentials.",
        ],
        "VALIDATION": [
            "Compare the request with the endpoint's documented schema.",
            "Validate required fields, data types, and formats.",
        ],
        "SERVER_ERROR": [
            "Inspect application logs and the stack trace.",
            "Review recent code changes near the failing endpoint.",
        ],
        "UNKNOWN": [
            "Collect the HTTP status code, full error message, and stack trace.",
            "Add logging around the failed request before diagnosing further.",
        ],
    }
    
    def suggest (self, state: AgentState) -> AgentState:
        """
        Suggest fixes for the final root cause.
        """
        
        root_cause = state.get("root_cause", "")
        failure_type = state.get("failure_type" , "UNKNOWN")
        
        fixes : List[str] = self.CAUSE_FIXES.get(
            root_cause ,
            self.CATEGORY_FIXES.get(
                failure_type , 
                self.CATEGORY_FIXES["UNKNOWN"]
                ) ,
        )
        
        # make a new list so state owns its own copy
        state["suggested_fixes"] = list(fixes)
        
        return state