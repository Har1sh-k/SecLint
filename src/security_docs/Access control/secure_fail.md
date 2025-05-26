# Fail Securely: Access Controls Must Fail Safe (No Silent Failure)

## Description of the Security Concern

**Access control** mechanisms (authentication, authorization checks, permission validations) should **fail securely**. “Failing securely” means that if something goes wrong – an error, exception, or any unexpected condition – the system should default to a secure state (typically denying access), rather than a less secure state. The opposite is “fail open,” where a failure in security controls inadvertently grants access or privileges. This is dangerous: a simple exception or logic bug can turn into a full security bypass if not handled properly.

A classic example is an authorization function that throws an exception; if the calling code doesn’t catch it and **securely handle it**, the application might skip the check and proceed as if the user has permission. MITRE’s CWE-636 defines Not Failing Securely (Failing Open) as a weakness where on error, the product *“falls back to a state that is less secure…, such as selecting the weakest encryption algorithm or using the most permissive access control restrictions.”*. In practice, this could mean *“allowing access”* when a check fails, which clearly violates the intended security.

**Silent failures** or missing checks are closely related issues. A silent failure is when an error in a security control is caught or ignored without enforcing the control. For example, if code catches an exception during an `isAuthorized()` call and simply logs it without denying access, the user might be granted access by default. A missing check is when a developer forgets to include an authentication/authorization check altogether in a code path – effectively treating an unverified user as verified, often due to logic oversight. Both scenarios lead to **Broken Access Control**, which is the top OWASP Top 10 web application vulnerability as of 2021.

To illustrate, consider the following scenario derived from OWASP’s guidance: A piece of code sets `isAdmin = true` initially, then tries to verify if the user is an admin, and on exception, it leaves `isAdmin` as true. The result is that if the check fails, the user ends up with admin privileges by default – a critical logic flaw. In OWASP’s words, *“design your security mechanism so that a failure will follow the same execution path as disallowing the operation.”*. In other words, if something goes wrong, **deny by default**.

Real-world incidents have occurred due to fail-open behavior. As an example, a CVE entry notes that a certain workflow product had a default configuration that **allowed all API requests without authentication** – essentially an access control that was not properly enforced (CVE-2020-13927). While this might be a configuration oversight, it echoes the principle: a system that doesn’t explicitly deny in the face of missing config or errors can open gaping holes.

## Best Practices to Fail Securely

To ensure access controls (and security mechanisms in general) fail safe, follow these best practices:

* **Default Deny:** Always initialize and design security flags/permissions with a safe default. For example, if your code is checking admin rights, start with `is_admin = False` (not true). Only set it to true **after** all checks pass. This way, if any step fails or an exception occurs, the default remains “deny access.” This approach follows the principle of least privilege and fail-safe defaults.

* **Catch Exceptions in Security Code:** Wrap security-critical operations (authentication checks, authorization lookups, etc.) in try/except blocks and handle failures by **rejecting the action**. For instance, if you query a database to verify a user’s role and the query throws an exception (say the DB is down), your code should treat that as a failed check (deny access), not ignore it. Log the error for visibility, but do not proceed as if the check succeeded. *All authentication and authorization controls should fail securely, never assume success on error*.

* **No Omission of Checks:** Ensure that every code path that requires an access control has the appropriate check. Use centralized middleware or decorators where possible so that it’s harder to “forget” a check on a critical path. For example, in a web app, have a central auth filter or require explicit annotation for open endpoints so that by default everything is protected unless specified public. Missing a check can be as bad as failing open.

* **Avoid Silent Catch-and-Continue:** Do not catch exceptions in security logic without taking appropriate action. Simply logging an exception and continuing normal execution is dangerous. Always consider what the exception means for security state. If an `isUserAuthenticated()` function cannot confirm authentication (due to error), the safest approach is to treat the user as *not authenticated*. Failing to do so may convert a transient error into an authentication bypass.

* **Fail Safe on External Integration Issues:** If your system relies on an external service for auth (e.g., OAuth token introspection, identity provider), plan for what happens if that service is unreachable or returns an error. The application should not automatically allow access in such cases. A common strategy is to have a grace period or a cached permission, but if that’s not applicable, the default must be to reject the request and show an error like “Authentication service not available,” rather than let the user in.

* **Test Failure Scenarios:** Include negative test cases and chaos testing for your security controls. For example, simulate a database exception during an authorization check in a QA environment and ensure the application indeed denies access. Also test that error messages don’t leak sensitive info – user-facing output on a security failure should be generic (e.g., “Access denied” or a redirect to login), while detailed errors are logged internally.

* **Use Framework Security Features:** Where possible, use security frameworks that are designed to fail safe. For instance, frameworks often have built-in authentication/authorization decorators or middleware; if configured correctly, they will default to deny on errors. Be cautious if writing low-level security code yourself – it’s easy to introduce logic that fails open if not careful.

By adhering to these practices, any failure in the security mechanism will result in **refusal of access or graceful degradation**, rather than a free pass for an attacker. This ensures that unforeseen issues or code bugs do not inadvertently turn off your application’s critical protections.

## Sample Insecure Code (Fail-Open Logic)

```python
def is_admin_user(user_id):
    is_admin = True  # Insecure default: assume admin until proven otherwise
    try:
        user = database.get_user(user_id)
        if user.role == 'admin':
            is_admin = True
        else:
            is_admin = False
    except Exception as e:
        log.error(f"Error checking admin status: {e}")
        # Security issue: exception is swallowed, is_admin remains True!
    return is_admin

# Usage
if is_admin_user(current_user_id):
    perform_admin_action()
```

In this example, the function `is_admin_user` attempts to determine if a user has admin privileges. The insecure aspects are:

* It initializes `is_admin = True`. This means the function **assumes success** (user is admin) by default.
* If any exception occurs during the database lookup (say the database is down, or the user\_id is invalid causing an error), the `except` block logs the error but does not set `is_admin` to false or stop the operation. The function will then return the value of `is_admin`, which in this case would still be `True` from the initial assumption.
* The calling code would interpret that as the user **is an admin** and proceed to `perform_admin_action()`, thereby **bypassing the check**.

This is a silent failure leading to a **fail open** condition – the error in the security check resulted in *unearned access*. As OWASP points out, security methods like this should be designed such that any exception results in denial of permission. In our code, the developer likely intended to default to not admin, but by incorrectly initializing to True and not handling exceptions correctly, the logic is reversed. This is obviously a serious flaw.

## Sample Secure Code (Fail-Safe Logic)

```python
def is_admin_user(user_id):
    try:
        user = database.get_user(user_id)
    except Exception as e:
        log.error(f"Error checking admin status: {e}")
        return False  # Fail securely: if we can't verify, assume not admin
    
    return user.role == 'admin'

# Usage
if is_admin_user(current_user_id):
    perform_admin_action()
```

In this corrected version, the code fails securely:

* We **default to denying access** if there's an exception. In the `except` block, we immediately return `False`. This means if the function cannot conclusively determine admin status (due to an error), it will err on the side of "not an admin".
* We removed the insecure initialization. Now `is_admin_user` only returns True if the user role is actually 'admin' and we were able to fetch the user without errors. Any failure yields False.
* The logic is simpler and safer: success case is explicitly checked, and any deviation (exception or non-admin role) leads to a False.

Now, if the database lookup fails or any unexpected issue occurs, the function returns False and the `perform_admin_action()` will not execute. The system thus preserves security by ensuring a failed check doesn’t equate to success. This aligns with the principle *“fail closed, not open”* – an error in a security control results in refusal of access. The user might encounter an error message or a denial, but that is preferable to unknowingly granting access. The error is logged for administrators to investigate, but from the user’s perspective, they simply don’t get unauthorized access.

This pattern should be applied to all security-relevant checks: **never assume or grant privileges on an exception or missing data**. For example, if a multi-factor authentication step fails to load, do not skip it—deny login. If an access control policy cannot be retrieved, default to the safest interpretation (usually no access).

## References

* OWASP Development Guide – *Fail Securely*: Recommends designing error handling such that security checks **follow the denial path on failure**, e.g., an `isAuthorized()` function returns false if an exception occurs.
* OWASP Secure Coding Practices: *“All authentication controls should fail securely.”* and *“When exceptions occur, fail securely.”* – Highlights that both auth logic and general exception handling must default to secure (no access) behavior.
* **MITRE CWE-636:** *Not Failing Securely (“Failing Open”)* – Defines the vulnerability of a system that on error falls back to less restrictive settings, such as allowing access when it shouldn’t. This CWE exemplifies the risk of silent failures in security mechanisms.
* OWASP “Fail Securely” article – Gives examples of how improper error handling in security code (like assuming true on exception) can introduce admin bypasses, and shows the corrected approach (initialize to false, etc.).
* **CVE-2020-13927:** An example where a product’s default configuration did not enforce authentication (a fail-open condition), allowing unauthenticated API access. Although a config issue, it underscores the importance of secure defaults.
