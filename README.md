# AI logistics project

## NOTE ABOUT THIS BRANCH
The purpose of this branch is to show the imagined end product for employers and interested parties. It is not a means of vibecoding the designated final version of the application. 
The goal is still to do the work myself with AI assistance, rather than to finish at a vibe-coded version.
Nevertheless, this can be thought of as how the final product will look, including the actual dashboard.
## Start the application

From the project root, run:

```bash
./start.sh
```

The script activates `backend/venv`, starts FastAPI at
`http://127.0.0.1:8000`, and starts the Vite frontend at
`http://127.0.0.1:5173`. Press Ctrl+C to stop both servers.

If the backend virtual environment or frontend `node_modules` directory is
missing, the script creates it and installs the corresponding dependencies.
