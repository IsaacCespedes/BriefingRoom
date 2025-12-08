# Technology-Specific Best Practices

This document provides best practices for Svelte, Python FastAPI, and crewAI.

---

## Svelte

-   **Component Co-location:** Keep component-specific logic, styles, and tests co-located within the same file or directory.
-   **Props:** Use props to pass data down to child components. Avoid using context for everything.
-   **Reactivity:** Leverage Svelte's reactive statements (`$:`).
-   **Stores:** Use Svelte stores for state that needs to be shared across multiple, unrelated components.
-   **Data Loading:** Use `+page.js` or `+layout.js` to load data for a page.

---

## Python FastAPI

-   **Async Everywhere:** Use `async` and `await` for all I/O-bound operations to keep your application non-blocking.
-   **Dependencies:** Use FastAPI's dependency injection system to manage resources like database connections.
-   **Pydantic Models:** Use Pydantic models for request and response validation, and to generate OpenAPI documentation.
-   **Routers:** Use `APIRouter` to structure your application into multiple, smaller modules.
-   **Background Tasks:** Use `BackgroundTasks` for long-running operations that shouldn't block the response.

---

## crewAI

-   **Define Roles Clearly:** Each agent should have a clear, well-defined role and backstory.
-   **Specific Tasks:** Assign specific, atomic tasks to each agent.
-   **Tools:** Provide agents with the necessary tools to perform their tasks.
-   **Sequential vs. Hierarchical:** Choose the appropriate process (sequential or hierarchical) based on the complexity of the task.
-   **Verbose Mode:** Use `verbose=True` during development to debug agent interactions.
