# Security Policy

## Supported versions

| Version | Supported |
| ------- | --------- |
| 1.0     | yes       |

## Reporting a vulnerability

Do not open a public GitHub issue. Email nishanthc264@gmail.com instead.

Include:
- What the vulnerability is
- How to reproduce it
- What the impact could be

You will get a response within 48 hours.

## Scope

Boss Package Manager runs desktop operations including dpkg and apt commands via PolicyKit. Report anything related to:

- Privilege escalation through the install/remove functionality
- Command injection in package field inputs
- Unsafe file operations during package building
- Any operation that runs as root via pkexec
