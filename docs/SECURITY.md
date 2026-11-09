# Security baseline

- Keep `.env`/tokens out of Git. Production fails with short or missing `API_TOKEN`. Protected inference APIs use constant-time key comparison.
- UI Nginx adds the API token only in the private proxy config, not in JS. This is service-to-service authentication, **not a login barrier for people opening the UI**. Put OIDC/SSO, HTTPS, rate limiting and firewall allowlisting at an ingress before LAN/public distribution.
- Bind API to loopback. Bind UI to the known LAN address only when appropriate and permitted. No outgoing network calls from inference and no arbitrary model URLs.
- The model checkpoint is a third-party Torch pickle format; checksum verification limits substitution, not inherent pickle risks. Use isolated and trusted build infrastructure.
- Do not log user image contents; no retained image or database. Limit payload bytes and decoded pixels. API and UI use read-only rootfs, cap drops, no-new-privileges, non-root users and tmpfs.
- ASGI body guards enforce byte limits before multipart parsing, including absent Content-Length. Reverse-proxy limits provide an additional line of defense. Concurrent connections still need perimeter rate limits.
- The current team-owned GitLab CI uses live `ssh-keyscan` output without separately pinned host-key verification; that is a CI security review item, not an API code issue. `ENV_FILE` must be a protected GitLab File variable; never print its contents or deploy with a placeholder API token.
- Benchmark high-load resource behavior before exposure. A semaphore bounds CPU work but does not replace upstream request limits and abusive-client protections.