# Missing Authorization hecks

## Explanation

Sometimes developers write temporary or placeholder code for authorization checks – for example, a function that is meant to validate a user's permissions but currently just returns `True` (allowing everyone). An **“always-true” access control stub** is a function or conditional that unconditionally allows access, often left in by mistake or during debugging. This means **all access control checks using that function will trivially pass**, effectively disabling security. The vulnerability here is that the intended authorization logic is not implemented at all: the check always returns true, so even users who should be forbidden can perform restricted actions. This is an example of *improper authorization implementation* (CWE-285) – the product incorrectly performs the authorization check by always succeeding. The result is similar to having no authorization checks: any user can exercise any functionality guarded by the stub. This flaw often slips in during development (e.g., a developer hard-codes `return True` to bypass checks for testing) and, if not removed, leads to a **fail-open scenario** where the system grants access by default. Attackers can exploit this by invoking privileged operations that would normally be protected, knowing that the access check will **always allow them**.

## Secure Coding Practices (OWASP)

* **Never Hard-Code Allow in Access Checks:** Authorization functions should have real logic. An access control function that simply returns `True` (or otherwise always allows) is fundamentally insecure. Follow the principle of **fail secure** – if for some reason the check cannot be performed, it should deny by default. In practice, ensure that your authorization routines actually verify roles/permissions and return false or throw an exception for unauthorized cases.
* **Remove Debug/Placeholder Code Before Production:** OWASP guidelines emphasize removing test or debug code not intended for production. An always-true stub is typically placeholder code. Such code must be replaced with actual security checks or removed entirely before deployment. Leaving it in is equivalent to leaving a backdoor open.
* **Use a Centralized Authorization Mechanism:** To avoid mistakes, use a well-designed, centralized authorization component or framework rather than ad-hoc stub functions scattered in the code. This way, it's less likely that a developer will create a trivial bypass. A central mechanism can enforce consistent policy (e.g., role checks) everywhere.
* **Code Reviews and Testing for Access Control:** Incorporate code review steps specifically to catch instances of stubbed logic (e.g., functions that return True/False without logic). Also, test the application’s endpoints with users of different roles to ensure that unauthorized access is truly prevented. This can catch an always-true check by observing that no matter the user, access was granted (a red flag).

## Insecure Code Example

```python
def check_access_stub(user, action):
    """Insecure: stub function that always grants access (no real validation)"""
    return True  # FIXME: This should check user's permissions, but currently allows everyone

# Usage in some part of the application
def delete_account(current_user, target_user):
    if check_access_stub(current_user, "delete_account"):
        print(f"User {current_user} deleted account {target_user}")
        # ... perform delete operation ...
```

In this insecure snippet, `check_access_stub` is a placeholder that **always returns `True`**, regardless of the user or action. The `delete_account` function uses this stub to decide if the current user can delete another user's account. Because the stub returns true unconditionally, **any user can delete any account**. This represents an *always-true access control check*. The code is essentially the same as having no check at all, which is an authorization vulnerability. An actual incident reflecting this issue is CVE-2025-47539, where a WordPress plugin had a permission check callback that always returned true, allowing unauthenticated users to call a privileged API.

## Secure Code Example

```python
# Define required roles for actions (as an example policy)
REQUIRED_ROLES = {
    "delete_account": "admin",    # Only admins can delete accounts
    "update_settings": "staff",   # Only staff role can update certain settings
}

def check_access(user, action):
    """Secure: checks if the user has the required role for the given action"""
    required_role = REQUIRED_ROLES.get(action)
    if required_role is None:
        # If the action is not defined in policy, deny by default (fail secure)
        return False
    # Only allow if user's role matches the required role
    return user.role == required_role

# Usage in application
def delete_account(current_user, target_user):
    if not check_access(current_user, "delete_account"):
        raise PermissionError("Unauthorized attempt to delete account!")
    print(f"User {current_user.name} (role={current_user.role}) deleted account {target_user}")
    # ... perform the deletion ...
```

In the secure code, `check_access` implements a simple role-based policy: it looks up the required role for the action and then compares it against the user's role. If the user's role is insufficient or if the action isn't recognized, it returns False (denies access). This ensures that, for example, only an admin can perform `"delete_account"`. The `delete_account` function uses `check_access` and will refuse to proceed if it returns False. This approach replaces the insecure stub with actual authorization logic, closing the hole. The code demonstrates **failing secure by default** — if an action isn't in the policy or the user doesn't meet the role, access is denied. It also follows the principle of least privilege by explicitly tying actions to roles. Importantly, all test or placeholder code (`return True` stubs) have been removed, as OWASP advises, so no debug backdoors remain in production.

## References

* **OWASP Secure Coding Practices – Access Control:** Access controls should **never default to allow**; they should fail securely (deny by default). Always implement real permission checks rather than hard-coded allowances. Remove any temporary *allow-all* code or debug hooks before deploying.
* **CWE-285: Improper Authorization:** Covers cases where an authorization check is performed incorrectly or not at all, which includes logic that always approves requests.
* **CWE-571: Expression Always True:** A code-level issue where a boolean expression is always true, often leading to flawed control flow (in this context, an authorization condition that always succeeds).
* **CVE-2025-47539:** Real-world example of an always-true authorization check. A WordPress plugin’s permission check function always returned true, allowing anyone (even unauthenticated users) to execute privileged operations. This highlights the critical danger of leaving such stubs in production.
