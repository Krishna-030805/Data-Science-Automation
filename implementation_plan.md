# Implementation Plan - Next.js + FastAPI Migration

We are going to migrate DataSense AI from a single Streamlit script into a professional, decoupled architecture. Since this is your first time with Next.js, we will build this step-by-step. Don't worry—I will handle the heavy lifting of writing the code, and I'll explain how it all connects.

## Goal Description
Transition the application to a modern SaaS stack:
1. **Backend (Python + FastAPI)**: We will keep your existing AI and Data Science logic exactly as it is, but wrap it in an API so the frontend can request data from it.
2. **Frontend (Next.js + React)**: We will create a brand new web interface with ultra-smooth animations, glowing metrics, and responsive layouts that look like a premium product.

## User Review Required

> [!IMPORTANT]
> This requires a significant restructuring of our folders. We will split the project into two distinct parts: a `backend/` folder for Python and a `frontend/` folder for Next.js.

> [!NOTE]
> Since you are new to Next.js, we will start with a very simple UI foundation, using **TailwindCSS** for styling and **Framer Motion** for those popping numbers and smooth animations.

## Open Questions

1. Do you have `Node.js` installed on your Windows machine? (We will need it to run the Next.js frontend). If not, we can easily install it.
2. Are you comfortable with me running terminal commands to scaffold the new Next.js project for you?

## Proposed Changes

### Phase 1: Restructuring the Backend
We will move the current `core/` logic into a new backend directory and replace `app.py` (Streamlit) with `main.py` (FastAPI).

#### [NEW] [backend/main.py](file:///e:/codes/Codes/ds_automator/backend/main.py)
* Create a FastAPI server that exposes our AI agents and data processing tools as REST endpoints.
* Endpoints to create:
  * `POST /upload`: Handles file uploads and returns the dataset overview.
  * `POST /profile`: Triggers the profiler agent.
  * `POST /train`: Triggers the ML engine.

#### [MODIFY] [core/](file:///e:/codes/Codes/ds_automator/core/)
* Move the entire `core/` folder inside the new `backend/` directory.

### Phase 2: Scaffolding the Frontend
We will initialize a Next.js project inside a new `frontend/` directory.

#### [NEW] [frontend/](file:///e:/codes/Codes/ds_automator/frontend/)
* I will run `npx create-next-app@latest frontend --typescript --tailwind --eslint --app` to generate the boilerplate.
* We will install `framer-motion` for our smooth animations and number pop effects.
* **Component Architecture**:
  * We will build reusable animated components like `<AnimatedMetric />` and `<QualityGauge />`.
  * We will recreate the layout with a sleek left-sidebar and a main content area.

### Phase 3: Wiring it Together
* We will connect the Next.js frontend to the FastAPI backend using standard HTTP requests (`fetch`).
* When a user uploads a file on the stunning new frontend, it sends it to the Python backend, does the math, and returns the results to be animated on screen.

## Verification Plan
1. **Start the Backend**: Run the FastAPI server (`uvicorn main:app --reload`) and verify endpoints respond via browser/swagger.
2. **Start the Frontend**: Run the Next.js development server (`npm run dev`) and ensure the beautiful new UI loads.
3. **End-to-End Test**: Upload a dataset from the new web UI, ensure Python processes it, and verify the frontend animates the incoming statistics perfectly.
