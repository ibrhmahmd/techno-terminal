# Research: System Contract Document

This document outlines the technical design decisions for displaying the System Capabilities Contract.

## Decision: Frontend-Only Static Rendering
- **Decision**: Storing the capabilities contract as a static Markdown file within the React frontend codebase and rendering it dynamically using a Markdown component (e.g. `react-markdown` if installed, or parsing it as structured JSON/HTML).
- **Rationale**: Since the copy describes the system's static modules, compiling it statically is faster, incurs zero database query overhead, and allows easy maintenance via source control.
- **Alternatives considered**: 
  - Backend API: A GET route returning the markdown text. Rejected because it introduces unnecessary network latency and backend complexity for static content.
  - Database Storage: Storing descriptions in a DB table. Rejected as it is overkill for a document representing a fixed client contract.

## Decision: Navigation Sidebar Placement
- **Decision**: Add a new link "Capabilities" to the main sidebar.
- **Rationale**: Provides one-click access for admins during live client meetings.
- **Alternatives considered**:
  - Settings page link: Rejected because it requires multiple clicks to access.
  - Reports tab: Rejected because this is a capabilities overview rather than a business report.
