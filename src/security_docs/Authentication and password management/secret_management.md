# Secret Management: Avoid Hardcoded Secrets in Code

## Explanation
Secrets such as passwords, API keys, database connection strings, and cryptographic keys should **never be hardcoded in source code**. Hardcoding secrets (i.e., embedding them in plaintext within code) is a serious security risk. If an attacker gains access to the source code (through insider threats, repository leaks, etc.), any embedded credentials are immediately compromised. OWASP notes that many organizations mistakenly keep secrets in code or config files, which greatly increases the likelihood of leaks. According to MITRE’s CWE-798, *“the product contains hard-coded credentials, such as a password or cryptographic key”*, making unauthorized access almost trivial for attackers. In addition to direct breaches, hardcoded secrets cannot be rotated or managed easily, compounding the risk if they leak.

**Impact:** Hardcoded secrets have led to real vulnerabilities. For example, a Python project **FreeTAKServer** was found to contain a hardcoded Flask secret key, allowing attackers to forge cookies and bypass authentication or escalate privileges. This illustrates how an embedded secret can undermine an entire security control. In general, any hardcoded credential (be it an admin password, encryption key, or API token) could be discovered by attackers (especially if code is public or reverse-engineered), leading to full system compromise.

## Secure Coding Practices (OWASP)

To manage secrets securely and avoid hardcoding, consider these best practices:

* **Use External Secret Storage:** Store secrets outside the source code. Common approaches include environment variables, configuration files not committed to source control, or dedicated secret management services (e.g., HashiCorp Vault, AWS Secrets Manager, GCP Secret Manager). For instance, an application can read an API key from an environment variable at runtime rather than a hardcoded string. *OWASP Secure Coding guidelines advise storing credentials in a secure location separate from the application logic*.

* **Employ Strong Access Controls on Secrets:** Limit who and what can access the secret store. The principle of least privilege should extend to secrets – for example, a database password stored in a config file should have file permissions such that only the application user can read it. Utilize OS-level protections or key management systems that enforce access control and auditing.

* **Enable Rotation and Versioning:** Your secret management solution should support rotating keys/passwords regularly and updating the application to use new secrets without code changes. Avoiding hardcoded secrets makes rotation feasible. This limits the damage window if a secret is compromised.

* **Encrypt Secrets at Rest:** If secrets are stored in files or databases, encrypt them using strong encryption. For example, use a key vault or at least encrypt config files with a master key (which itself is stored securely). This ensures that even if the storage location is accessed, the secrets are not immediately exposed in plain text.

* **Detect Leaks Early:** Implement scanning tools (such as trufflehog or git-secrets) in your development pipeline to catch any hardcoded secrets before code is committed. These tools can prevent accidental introduction of secrets into the codebase by developers.

* **Avoid Defaults and Document Usage:** Do not rely on default credentials or keys. Ensure that any sample or default config is overridden in production with secure values. Document how developers should supply secrets (e.g., via env variables or a secrets manager) so that hardcoding isn’t done out of convenience.

By following these practices, secrets are managed centrally and **not embedded in code**, greatly reducing the risk of accidental exposure.

## Insecure Code Example

Below is an example of **insecure Python code** where a secret is hardcoded. This code uses a hardcoded API token string to authenticate to an external service:

```python
import requests

# Insecure: Hardcoded API token (secret) in code
API_TOKEN = "ABC123SECRET_TOKEN_XYZ"  # hardcoded secret

response = requests.get(
    "https://api.example.com/data",
    headers={"Authorization": f"Bearer {API_TOKEN}"}
)
```

In this example, `API_TOKEN` is a sensitive credential embedded directly in the source. This is dangerous because anyone with access to the code (or the version control history) can see the token. If this code were published publicly or leaked, the secret would be exposed. An attacker could misuse the token to access the external service with potentially full privileges. Moreover, rotating the token would require changing the source code and deploying again, which is error-prone and not scalable.

## Secure Code Example

The following Python code demonstrates a **secure approach** using an environment variable to supply the secret at runtime, rather than hardcoding it:

```python
import os
import requests

# Secure: Load API token from environment or config, not from hardcoded value
API_TOKEN = os.environ.get("API_TOKEN")  # e.g., set in server environment or .env file
if API_TOKEN is None:
    raise RuntimeError("API_TOKEN not set in environment")

response = requests.get(
    "https://api.example.com/data",
    headers={"Authorization": f"Bearer {API_TOKEN}"}
)
```

**Why is this secure?** The secret value is not present in the source code. Instead, it’s read from an external source (an environment variable in this case). In deployment, the `API_TOKEN` environment variable can be provisioned securely (for example, through container orchestration secrets, or set on the host with proper permissions). This way, if the code is leaked or open-sourced, the secret itself remains confidential. The application will obtain the secret at runtime without ever storing it in the code repository. This approach also makes rotation simpler: update the environment variable and restart the app, without any code change.

In a more advanced setup, the code might fetch the secret from a secret management service or key vault at startup. For example, one could integrate with AWS Secrets Manager or Vault API to retrieve the secret. The key point is that the secret’s storage and lifecycle are decoupled from the application’s source code. Any failures to retrieve the secret (e.g., missing environment variable) in the above code result in an error (`RuntimeError`), which is **fail-secure** – the application will not proceed without a valid secret, rather than running with some insecure default.

## References

* OWASP Cheat Sheet Series: *Secrets Management* – Highlights the risks of plaintext secrets in code and the need for centralized secret storage.
* OWASP Secure Coding Practices – *Authentication Credentials*: *“Authentication credentials for accessing services external to the application should be stored in a secure store.”* This reinforces keeping secrets out of code.
* **MITRE CWE-798:** *Use of Hard-coded Credentials* – Definition of the weakness and its consequences.
* **CVE-2022-25510 (FreeTAKServer):** Hardcoded Flask secret key in a Python project led to authentication bypass. (Example of real-world impact of hardcoded secret.)
