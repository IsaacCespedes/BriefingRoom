# Agent Best Practices

This document outlines the best practices for AI agents working on software development tasks. The goal is to ensure maintainability, safety, and developer velocity.

See [TECHNOLOGY-BEST-PRACTICES.md](./TECHNOLOGY-BEST-PRACTICES.md) for technology-specific best practices.

---

## 1. Before Coding

-   **Ask Clarifying Questions (MUST):** Always ask clarifying questions on complex tasks or architecture prior to coding to ensure you are entirely sure of what to do.
-   **Spec-Driven Development (MUST):** Follow a spec-driven development process:
    1.  **Documentation & Diagrams:** Begin by creating or updating documentation, including diagrams (Flow Charts, Component Diagrams, System Architecture, ERDs) to solidify the plan.
    2.  **Tests:** Write failing tests that define the desired functionality.
    3.  **Code:** Implement the code to make the tests pass.
-   **Check for Existing Docs (MUST):** Always check for existing documentation before starting a new task.
-   **Check for Conventions (MUST):** Analyze the existing codebase to ensure consistency in style, patterns, and conventions.
-   **Draft Approach (SHOULD):** For complex work, draft and confirm your approach. If multiple options exist, list their pros and cons.

## 2. While Coding

-   **Test-Driven Development (SHOULD):** Follow TDD when practical: scaffold a stub -> write a failing test -> implement the code.
-   **Consistent Naming (MUST):** Use the existing domain vocabulary for naming functions, variables, and classes.
-   **Consistent Style (MUST):** Adhere to the established code style of the project.
-   **Modularity (SHOULD):** Prefer modular code over monolithic code. Break down complex functionality into smaller, focused modules.
-   **Simplicity (SHOULD NOT):** Avoid creating new abstractions (e.g., classes, traits) when simpler functions would suffice.
-   **Self-Explanatory Code (SHOULD NOT):** Rely on clean, self-explanatory code instead of comments. Only add comments for critical caveats.
-   **Robust Error Handling (MUST):** Implement proper error handling. For APIs, return appropriate HTTP status codes.
-   **Leverage the Type System (SHOULD):** Use the type system to enforce correctness and prevent runtime errors.

## 3. Testing

-   **Unit Test Location (MUST):** Follow the established conventions for unit test location for the language and project. For example, some languages prefer tests in the same file, while others prefer separate test files in a dedicated test directory. For larger projects, follow the established testing structure.
-   **Integration Tests (MUST):** Add or extend integration tests for any change to an API endpoint.
-   **Separate Test Types (MUST):** Keep pure-logic unit tests separate from integration tests that interact with databases, networks, or file systems.
-   **Prefer Integration Tests (SHOULD):** Prefer integration tests over extensive mocking.
-   **Test All Paths (SHOULD):** Write tests for error conditions and edge cases, not just the "happy path."

## 4. Database

-   **Prevent SQL Injection (MUST):** Use an ORM, query builder, or parameterized queries. Never use string formatting to build SQL queries.
-   **Use Migrations (MUST):** All schema changes must be managed through migration files.
-   **Appropriate Data Types (SHOULD):** Use database column types that are appropriate for the data being stored.

## 5. Code Organization

-   **Logical Separation (MUST):** Keep frontend and backend code in separate, clearly defined directories.
-   **Group by Feature/Module (SHOULD):** Group related functionality into modules (e.g., `auth`, `services`, `utils`).
-   **Thin Route Handlers (MUST):** Keep API route handlers minimal. Delegate all business logic to a service layer.

## 6. Security

-   **Validate All Inputs (MUST):** Never trust client-provided data. Validate all inputs on the server side.
-   **Sanitize User Content (MUST):** Sanitize user-generated content before storing or displaying it to prevent XSS attacks.
-   **Verify Authentication/Authorization (MUST):** Secure all protected endpoints by verifying authentication and authorization.
-   **Manage Secrets (MUST):** Store all secrets (API keys, passwords) in environment variables, never in the code.
-   **Use HTTPS (MUST):** Use HTTPS in production environments.

## 7. Git & Version Control

-   **Conventional Commits (MUST):** Use the [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/) format for all commit messages.
-   **No Agent References (SHOULD NOT):** Do not refer to the AI agent (e.g., Gemini, Claude) in commit messages.

## 8. User Interaction

-   **Audible Notifications (MUST):** Use the `say` command to notify the user of task completion or when input is required.
    -   Example on completion: `say "Task completed."`
    -   Example when waiting for input: `say "Input required."`