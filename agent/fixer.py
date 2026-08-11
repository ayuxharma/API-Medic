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
        "User lacks required permission": [
    "Check which permission the endpoint requires.",
    "Grant the required permission only if the user should have access.",
    "Verify that the permission check uses the correct user identity.",
],
"Token has insufficient scope": [
    "Inspect the scopes included in the access token.",
    "Request a token containing the scope required by the endpoint.",
    "Verify that the API checks the intended scope name.",
],
"User role is not allowed for this resource": [
    "Check which roles are allowed to access the resource.",
    "Verify that the user has been assigned the correct role.",
    "Review the role-based access-control policy for the endpoint.",
],
"Database connection is unavailable": [
            "Verify that the database server is running and reachable.",
            "Check the database hostname, port, username, and connection URL.",
            "Inspect firewall rules, network access, and connection-pool limits.",
        ],
        "Database constraint was violated": [
            "Inspect the database constraint named in the error message.",
            "Check whether the submitted value already exists or references missing data.",
            "Validate unique, foreign-key, and required values before executing the query.",
        ],
        "Database query execution failed": [
            "Inspect the SQL or ORM query reported in the stack trace.",
            "Verify table names, column names, parameters, and SQL syntax.",
            "Run the query in a safe development environment to reproduce the failure.",
        ],
        "Database deadlock occurred": [
    "Keep transactions short and avoid unnecessary work while holding locks.",
    "Access shared tables and rows in a consistent order across transactions.",
    "Add a bounded retry with backoff for transactions selected as deadlock victims.",
],
"Database lock wait timed out": [
    "Identify the transaction holding the required database lock.",
    "Reduce long-running transactions and commit or roll them back promptly.",
    "Check whether missing indexes are causing queries to lock more rows than necessary.",
],
"Transaction serialization conflict occurred": [
    "Retry the complete transaction using a bounded retry policy.",
    "Review whether the current transaction isolation level is required.",
    "Use version checks or optimistic concurrency controls for conflicting updates.",
],
    }

    
    CATEGORY_FIXES = {
        "AUTHENTICATION": [
            "Check the Authorization header and token lifecycle.",
            "Verify authentication configuration and credentials.",
        ],
        "AUTHORIZATION": [
            "Check the user's roles, permissions, and token scopes.",
            "Verify the endpoint's access-control policy.",
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
        "DATABASE": [
            "Inspect database logs and application database exceptions.",
            "Verify database connectivity, schema constraints, and query correctness.",
        ],
        "DATABASE_CONCURRENCY": [
    "Inspect active transactions, locks, and database wait events.",
    "Review transaction duration, lock order, isolation level, and retry behavior.",
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