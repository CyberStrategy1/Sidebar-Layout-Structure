Updated Knowledge Snippets (Context for the AI)
Use these snippets in your prompts to provide the AI with the necessary context for building this enterprise-grade platform.

On Project Start:
"I am building a multi-tenant SaaS platform called 'Aperture Enterprise'. The application will have a distinct customer-facing portal and a separate administrative console."

On User Management:
"We are using the Supabase integration for authentication. The database schema must be multi-tenant, meaning all data tables like 'tech_stack' or 'scan_results' must have an 'organization_id' column to ensure data is isolated using Row-Level Security."

On Admin Features:
"This feature is for the Admin Console, which is only accessible to platform operators. It should display data from all customer accounts."

On Customer Features:
"This feature is for the Customer Portal. All database queries written for this page must be filtered to only show data for the currently logged-in user's organization."

On API Health:
"This module is for the Admin Console's API Health Dashboard. It needs to perform periodic 'heartbeat' checks on external APIs and display their operational status."