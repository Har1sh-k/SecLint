# Missing Role-Based Authorization for Privileged Actions

## Explanation

In **role-based authorization**, certain high-privilege actions (such as creating or deleting users, or changing user roles) should only be allowed for users with specific roles (e.g., administrators). A vulnerability arises when the code does **not check the user's role or privileges** before performing these sensitive actions. This means any authenticated user (or even unauthenticated in worst cases) could invoke privileged functionality that should be restricted. The application essentially **fails to perform an authorization check** when an actor attempts to access a privileged resource or operation. As a result, attackers can escalate their privileges or perform unauthorized operations by simply calling the privileged function or endpoint, since the software does not verify the user’s role (for example, updating another user's role without being an admin). This scenario is a **Broken Access Control** issue; it violates the principle of least privilege by allowing actions beyond a user's permitted scope and can lead to severe security breaches.

## Secure Coding Practices (OWASP)

* **Enforce Role-Based Access on Every Request:** The system must enforce authorization checks on every request for privileged actions. Do not assume that just because a user is authenticated, they can perform admin-level tasks – always verify their role/permissions for each action.
* **Restrict Privileged Functions to Authorized Roles:** Ensure that **protected functions and administrative URLs are only accessible to authorized roles**. For example, only users with an "Admin" role should be able to invoke the user role update function. All other users should be denied by default.
* **Fail Securely (Default Deny):** The access control mechanism should **fail securely** – if there is any doubt or any error retrieving authorization info, the system should deny access. Never allow access just because a role check fails to execute; a missing or broken check should result in no access, not full access.
* **Centralize and Document Access Control:** Use a single, well-tested component or service for authorization decisions across the app, and define an **Access Control Policy** documenting roles and privileges. According to OWASP, having a clear policy of the application's business rules and authorization criteria ensures proper provisioning and control of access. This makes it easier to manage roles (like Admin, User, Moderator) and verify that each privileged action explicitly checks the user's role against allowed roles.

## Insecure Code Example

```python
USER_ROLES = {"alice": "user", "bob": "admin"}

def update_user_role(current_user, target_user, new_role):
    """Insecure: allows any user to update anyone's role without checking their privileges"""
    # No check for current_user's role
    database.update_role(target_user, new_role)
    print(f"{current_user} changed {target_user}'s role to {new_role}")

# Example usage:
current_user = "alice"  # alice is a regular user, not an admin
update_user_role(current_user, "victim_user", "admin")
# In this insecure design, alice (not an admin) can promote victim_user to admin with no restriction.
```

In the above insecure code, the function `update_user_role` does **not verify** that `current_user` has an administrator role before altering another user's role. Any user, even one without admin rights, can directly call this function to escalate privileges. This lack of a role check exemplifies **Missing Authorization** (CWE-862).

## Secure Code Example

```python
USER_ROLES = {"alice": "user", "bob": "admin"}

def update_user_role(current_user, target_user, new_role):
    """Secure: only allow admins to update another user's role"""
    # Check that current_user has an admin role before proceeding
    if USER_ROLES.get(current_user) != "admin":
        raise PermissionError(f"User {current_user} is not authorized to perform this action.")
    database.update_role(target_user, new_role)
    print(f"{current_user} (admin) changed {target_user}'s role to {new_role}")

# Example usage:
current_user = "alice"
try:
    update_user_role(current_user, "victim_user", "admin")
except PermissionError as e:
    print(e)  # Outputs: "User alice is not authorized to perform this action."
```

In the secure code, the `update_user_role` function checks the current user's role and only proceeds if the user is an **admin**. If not, it raises an error or otherwise prevents the action. This implements **role-based authorization**: only authorized roles can perform the privileged update. The code follows the OWASP guideline to **restrict access to protected functions to authorized users only**, and it fails closed (denies access) for non-admins, which is a secure default.

## References

* **OWASP Secure Coding Practices – Access Control:** Enforce checks on every request; restrict admin functions to authorized users. Fail secure (deny by default) if authorization cannot be verified. Develop an Access Control Policy defining roles and permissions.
* **CWE-862: Missing Authorization:** Describes failures to verify that a user has permission to perform an action.
* **CVE-2024-1716:** Example of a real vulnerability where a missing capability (role) check in a plugin allowed low-privileged users to perform an admin action. This highlights the risks of not implementing role-based checks.
