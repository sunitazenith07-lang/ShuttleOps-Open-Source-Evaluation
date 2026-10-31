# Architecture Notes
    The application follows a modular architecture, separating business logic, service-layer operations and data handling for better maintainability and scalability. Changes were limited to service.py, keeping the existing architecture intact.
## Project map
    The project is organized into modular components with service.py handling core business logic and service-level operations.
## Data model

## Data flow
    The existing data model and schema were retained without any kind of structural modifications. Changes were limited to the service layer (service.py) preserving existing data relationships and field definitions.
## Storage design
    The existing storage mechanism and data persistence strategy were retained without changes. All modifications were confined to service.py, with no alterations to database schemas (tests), storage structures, or persistence configurations.
## Diagram
        Client / API Request
                |
                v
        Application Layer
                |
                v
          Service Layer
          (service.py)
                |
                v
        Business Logic
                |
                v
        Data Access Layer
                |
                v
          Data Storage
                |
                v
          API Response

## Three improvements suggested
1. Issue 1 – ETA and input validation
2. Issue 2 – Partner eligibility and capacity
3. Issue 3 – Duplicate cancellation events