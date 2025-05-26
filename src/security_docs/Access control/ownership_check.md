# Missing Ownership Check for User-Specific Resource Access

## Explanation

Web applications often allow users to access or manipulate their own resources (for example, viewing or editing their profile, documents, or account data). A vulnerability occurs when the application **does not verify that the acting user owns the resource or has permission to access it**. This is commonly known as an **Insecure Direct Object Reference (IDOR)**, a type of Broken Access Control. In such cases, an attacker can simply change a parameter or URL (such as a user ID or record ID) to another value and gain access to someone else’s data because the server fails to check ownership. In other words, the authorization mechanism does not prevent one user from accessing or modifying another user's data by supplying a different resource identifier. This missing ownership check can lead to **data breaches or unauthorized modifications** – for example, one user might view or edit another user's profile, or download someone else's files, by manipulating identifiers. This weakness undermines data confidentiality and integrity, since users can **escalate privileges horizontally** (gaining access to peer users’ data).

## Secure Coding Practices (OWASP)

* **Enforce Object-Level Access Control:** The application must validate that the current user is authorized for the specific record or object being accessed. OWASP recommends restricting **direct object references** (like database IDs) to only those users who are authorized. In practice, every time a user requests a resource by an ID, the server should check that the resource belongs to that user (or the user has an appropriate role to access it).
* **Use Server-Side Authorization Checks with Trusted Data:** Do not rely on user-supplied identifiers alone for access control. Use server-side information (such as the user’s session or token data) to determine which objects they can access. For example, fetch user-specific data with a query that includes the user's unique ID in the WHERE clause, or verify that `current_user.id == requested_object.owner_id` before returning the object. This ensures the decision is based on trusted server-side attributes, not just what the user provides.
* **Implement Least Privilege for Data Access:** Each user should only be able to access their own records by default. If other access is needed (e.g., an admin viewing others’ data), explicitly grant that in the code. All other access attempts should be denied. This aligns with OWASP guidance to **enforce authorization on every request** for sensitive data and to allow access to application data only by authorized users.
* **Secure Indirect References or Use Random IDs:** If possible, avoid using sequential or predictable IDs for sensitive objects. Use **secure indirect object references** (e.g., random UUIDs or mapping IDs to session-specific values) so that guessing an ID is not trivial. In any case, **never omit the server-side check**; even unpredictable IDs must be verified for ownership on the server.

## Insecure Code Example

```python
# A simple in-memory store of user profiles
user_profiles = {
    101: {"name": "Alice", "email": "alice@example.com", "owner_id": 101},
    102: {"name": "Bob", "email": "bob@example.com", "owner_id": 102}
}

def get_profile(current_user_id, profile_id):
    """Insecure: returns profile data without checking ownership"""
    # No check that current_user_id matches the profile's owner_id
    return user_profiles.get(profile_id)

# Example: Alice (user_id 101) attempting to access Bob's profile (user_id 102)
current_user_id = 101
profile = get_profile(current_user_id, 102)
print(profile)  # Outputs Bob's profile data, even though Alice is not the owner.
```

In this insecure example, the function `get_profile` takes a `profile_id` and returns the data without verifying that the `current_user_id` is allowed to access that profile. As shown, Alice (101) can retrieve Bob's profile (102) simply by requesting it, because there's no **ownership check**. This is a classic IDOR scenario: the system fails to ensure that the user requesting the data is its owner or otherwise authorized.

## Secure Code Example

```python
def get_profile(current_user_id, profile_id):
    """Secure: returns profile data only if the requesting user is the owner"""
    profile = user_profiles.get(profile_id)
    if profile is None:
        return None  # profile not found
    if profile["owner_id"] != current_user_id:
        raise PermissionError("Access denied: you do not own this resource.")
    return profile

# Example: Alice (101) attempting to access Bob's profile (102)
current_user_id = 101
try:
    profile = get_profile(current_user_id, 102)
except PermissionError as e:
    print(e)  # "Access denied: you do not own this resource."
```

In the secure version, `get_profile` checks that the profile's `owner_id` matches the `current_user_id` of the requester. If they don't match, it denies access. This ensures a user can only retrieve their own profile (unless explicitly allowed otherwise). By enforcing this **ownership check** on the server side, we prevent users from accessing others' data. The code adheres to OWASP best practices by **restricting direct object references to authorized users only** and using a server-side validation of ownership before returning data. Even if an attacker guesses or manipulates a `profile_id`, the server will not divulge the data unless the user is authorized for that object.

## References

* **OWASP Secure Coding Practices – Access Control:** Restrict direct object references (IDs) to only authorized users. Always perform server-side authorization checks using trusted data (e.g., session user ID) to confirm the user’s right to access the requested object.
* **CWE-639: Authorization Bypass Through User-Controlled Key:** Describes failures to enforce ownership, where modifying a key or ID allows one user to access another's record. This is the classic pattern behind IDOR vulnerabilities.
* **CVE-2024-28320:** An example IDOR vulnerability in a real application – by altering a user ID parameter, an attacker could gain unauthorized access and modify another user’s data. This real-world case underscores the need for strict ownership validation.