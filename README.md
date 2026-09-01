# AI logistics project

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
