
# Password Hashing: Enforce Secure Hash Functions for Passwords

## Description of the Security Concern

Storing user passwords safely is critical. One common weakness is using **insecure or insufficient hashing algorithms** for passwords, or not hashing passwords at all. Insecure hashing means using outdated or fast hashes (like MD5 or SHA-1) or hashing without salts/pepper, which makes passwords vulnerable to cracking. According to OWASP guidelines, passwords must be stored using *“cryptographically strong, one-way salted hashes”*. Using a weak hash or no salt significantly reduces the effort needed for attackers to recover the original passwords via brute force or precomputed lookup (e.g., rainbow tables).

**Why are MD5/SHA1 insecure for passwords?** Algorithms like MD5 and SHA-1 are considered cryptographically broken or weak for modern standards. More importantly, they were designed to be **fast**, which is the opposite of what you want for password storage. A fast hash allows attackers to attempt billions of guesses per second on modern hardware. OWASP notes that password hashes should be computationally slow to thwart offline cracking – *“unlike algorithms such as MD5 and SHA-1, which were designed to be fast”*. Additionally, unsalted hashes mean identical passwords result in identical hashes, enabling trivial lookup attacks.

**Impact:** Insecure password hashing leads to many real breaches. For example, CVE-2022-21800 describes a system that hashed passwords with unsalted MD5, which allowed attackers to easily crack those hashes. In another case, Opencast < 8.1 used unsalted MD5 for passwords, and an upgrade was needed to move to bcrypt to properly secure them. These cases underscore that relying on weak or unsalted hashes can make password databases an easy target – once obtained, an attacker can crack a large portion of passwords in a short time.

Using **insecure hash functions** or configurations is categorized by CWE-916: *“The product generates a hash for a password, but uses a scheme that does not provide a sufficient level of computational effort to make password cracking infeasible.”*. In practice, this means if your code is using a single round of a fast hash (like a single MD5, SHA-1, or even a single SHA-256) for storing passwords, it is not providing adequate security.

## Best Practices for Secure Implementation

To securely handle password hashing, developers should follow these best practices:

* **Use Strong, Adaptive Hashing Algorithms:** Employ password hashing functions that are designed to be *slow* and *adaptive*. Current recommendations (per OWASP Password Storage Cheat Sheet) include algorithms like Argon2id, bcrypt, scrypt, or PBKDF2-HMAC (with a high iteration count). These algorithms incorporate work factors (cost parameters) that can be tuned to increase computation time, thereby slowing down brute-force attacks. Avoid deprecated or fast hashes for password storage (MD5, SHA-1, unsalted SHA-256, etc. are **not** acceptable).

* **Incorporate Salt for Uniqueness:** Always hash passwords with a *per-user random salt*. A salt is a random value added to each password before hashing; it ensures that identical passwords do not produce the same hash across users or systems. Most modern hash libraries (bcrypt, Argon2, etc.) automatically handle salts. If using lower-level functions, generate a cryptographically secure random salt (e.g., 16+ bytes from `os.urandom()` or Python’s `secrets` module). Storing the salt alongside the hash is fine (it's not secret) – its purpose is to prevent precomputed attacks and force attackers to crack each hash individually.

* **Use Pepper for Additional Security (Optional):** A pepper is a secret key added to hashing in addition to salt. Unlike salts, a pepper is the same for many or all hashes and is kept secret (like in application config). If an attacker obtains the hash database but not the pepper, it adds another layer of defense. However, pepper management (rotation, storage) must be handled carefully. This is an extra layer *after* implementing strong hashing and salting, not a substitute.

* **Leverage Established Libraries/Frameworks:** Do not write your own low-level password hashing logic if well-vetted implementations are available. Use libraries like `bcrypt` (PyPI), `argon2-cffi`, or high-level framework utilities (e.g., Django’s `make_password`/`check_password`, Flask’s Werkzeug security functions) which are battle-tested. These handle salting and proper algorithm parameters for you. Always verify the library’s default parameters align with current best practice (for example, a bcrypt default cost of 12 is generally good; Argon2 default settings as recommended by OWASP).

* **Enforce Hashing in Code Reviews/Linting:** Ensure that any code handling user passwords uses the approved secure hashing method. No plaintext storage, no use of MD5/SHA1. Consider adding linters or hooks to flag the use of insecure functions (e.g., flag any `hashlib.md5()` usage on a variable named "password"). Educate the team that under no circumstances should passwords be stored or logged in plain or with weak hashes.

* **Upgrade Legacy Hashes:** If you have an existing system with older hashes, implement a gradual upgrade strategy. For instance, on user login, if you detect an old hash (MD5/SHA-1, etc.), re-hash the password with the new algorithm and store it. This way, over time users’ hashes get upgraded. Also, for compliance, have a policy to increase work factors periodically (e.g., bcrypt rounds) as computing power grows.

By strictly using robust hashing mechanisms, even if an attacker steals the password hash database, cracking the passwords should be computationally infeasible or at least extremely time-consuming. This significantly protects users from password reuse attacks and the organization from breach escalation.

## Sample Insecure Code (Weak Password Hashing)

```python
import hashlib

def store_password(username, password):
    # Insecure: using MD5 (fast, broken hash) with no salt for password
    hash_hex = hashlib.md5(password.encode()).hexdigest()  # MD5 is not secure for passwords!
    save_password_hash(username, hash_hex)
```

In this example, the `store_password` function takes a plaintext password and hashes it using MD5. **What's wrong?** MD5 is a very fast and now broken hashing algorithm, unsuitable for password security. There is also no salt added. An attacker who obtains `hash_hex` for multiple users might quickly crack many of them using brute-force or lookup tables, because MD5 hashes of common passwords are widely known. Furthermore, identical passwords will produce identical MD5 hashes, making the attacker’s job easier (they can detect if multiple users have the same password, etc.). This code violates the principle of sufficient computational effort for password storage (CWE-916).

Even using a faster modern hash like a single SHA-256 would be problematic here – not just MD5. The core issues are lack of a slow, work-factor based algorithm and missing salt. The result is an **insufficient defense** against offline cracking.

## Sample Secure Code (Strong Password Hashing)

```python
import bcrypt  # uses strong adaptive hashing (bcrypt algorithm)

def store_password(username, password):
    # Secure: use bcrypt with automatic salt
    password_bytes = password.encode()                              
    hashed = bcrypt.hashpw(password_bytes, bcrypt.gensalt())  # generates salt and hashes with bcrypt
    save_password_hash(username, hashed.decode())  # store the hash (as printable string)

def verify_password(username, password_attempt):
    # Retrieve the stored hash (as bytes) for the user from DB:
    stored_hash = get_password_hash(username).encode()  
    return bcrypt.checkpw(password_attempt.encode(), stored_hash)
```

In this secure example, the code uses the **bcrypt** library to hash passwords. Bcrypt automatically handles salting and applies a work factor (cost). By default, `bcrypt.gensalt()` will generate a random salt and the hashing algorithm will run a number of rounds (cost factor), making the hash computation deliberately slow. The stored hash includes metadata about the salt and cost, so `checkpw` can verify a password attempt.

**Why is this secure?** Bcrypt is a proven algorithm designed for password hashing. It’s adaptive (we can increase the cost factor to adjust hashing time) and incorporates a salt to produce unique hashes even for identical passwords. An attacker obtaining these hashes would face a much more difficult task: each password hash would require a computationally expensive brute-force, and the cost can be tuned to be high enough to thwart practical cracking. Unlike MD5 which can be computed millions of times per second on modern hardware, bcrypt with a decent cost might only be computed a few hundred times per second, drastically slowing an attacker. This follows the OWASP guidance to use one-way salted hashes with significant computational effort.

*Note:* Instead of `bcrypt`, one could use Python’s built-in `hashlib.pbkdf2_hmac()` for a similar effect (PBKDF2 algorithm), or higher-level frameworks which abstract this. The key is that a proper algorithm (bcrypt/PBKDF2/scrypt/Argon2) is used **with salt and an appropriate number of iterations**. Also, ensure to handle encoding/decoding properly, and store the hash (and salt if needed) in the database. Never store the plaintext password or a simple unsalted hash.

## References

* OWASP Secure Coding Practices (Authentication): *“If your application manages a credential store, use cryptographically strong one-way salted hashes.”* – Emphasizes storing passwords with strong salted hashing.
* OWASP Password Storage Cheat Sheet – Recommends modern algorithms (Argon2id, bcrypt, scrypt, PBKDF2) and notes that **fast hashes like MD5 or SHA-1 are inadequate for passwords**.
* **MITRE CWE-916:** *Use of Password Hash with Insufficient Computational Effort* – Describes the weakness of using hashing schemes that are too fast or weak, making password cracking easier.
* **CVE-2022-21800:** Example vulnerability where a product used unsalted MD5 for passwords, allowing attackers to crack them easily.
* **CVE-2020-5229 (Opencast):** Another case where upgrading from MD5 to bcrypt was necessary to fix insecure password hashing.