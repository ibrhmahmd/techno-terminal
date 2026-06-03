# Quickstart

This audit brings the Groups Directory module up to code quality standards and ensures production stability.

### What Changed
1. **Broken Links Fixed**: The legacy endpoints for `/search` and `/by-type` were removed. Other endpoints are now properly connected to the `filter_groups` engine.
2. **Safer Execution**: The `/enriched` endpoint is now paginated, protecting backend memory.
3. **Robust Filtering**: `filter_groups` now supports checking capacity, instructor presence, and inactive inclusion, allowing the frontend to drop older bespoke API calls and build one unified filter view.
4. **Data Type Strictness**: The API schemas use strictly-defined classes rather than generic `dict` shapes.
