# Takes a Village - Backend Service

This is the backend service for the "Takes a Village" project. It is a Python application built with Flask and Flask-SocketIO.

## Tech Stack

* **[Python](https://www.python.org/)**: A high-level, general-purpose programming language.
* **[Flask](https://flask.palletsprojects.com/)**: A lightweight WSGI web application framework.
* **[Flask-SocketIO](https://flask-socketio.readthedocs.io/)**: Provides Socket.IO integration for Flask applications, enabling real-time, bidirectional communication between web clients and servers.
* **[Eventlet](https://eventlet.net/)**: A concurrent networking library for Python that allows you to change how you run your code, not how you write it. It is used here as a web server for Flask-SocketIO.
* **[MySQL Connector/Python](https://dev.mysql.com/doc/connector-python/en/)**: A driver for connecting Python programs to MySQL databases.

## Project Structure

```
service/
├── models/         # Data models for the application
├── names/          # Files for generating names
├── resolvers/      # Resolve the phases and back-forth trading
├── actions/        # Player actions as command type objects
├── constants/      # Game rules for costs, starting inventory
├── venv/           # Python virtual environment
├── app.py          # Main Flask application file
├── db.py           # Database connection and management
├── game.py         # Core game logic
└── setup.sh        # Setup script for the virtual environment
```

## Getting Started, (non Docker deployment)

To get the backend service up and running, follow these steps:

1. **Prerequisites: MySQL Database (Optional)**

    Before launching the service, you need to have a MySQL server running and accessible. The service requires a database to store its data.

2. **Create `config.json`**:

    Create a file named `config.json` in the `service/` directory. This file will hold your database credentials and a secret key for Flask. Use the following template:

    ```json
    {
      "db": {
        "user": "root",
        "password": "your_real_password",
        "host": "127.0.0.1",
        "database": "village_db"
      },
      "flask": {
        "secret_key": "complex_random_string_here"
      }
    }
    ```

    **Important**: Replace `"your_real_password"` with your actual MySQL password and consider changing the `"secret_key"` to a unique, complex string.

3. **Set up the Virtual Environment**:

    The `setup.sh` script will create a Python virtual environment and install all the necessary dependencies. To run it, use the `source` command:

    ```bash
    source setup.sh
    ```

    This will create a `venv` directory, activate the virtual environment, and install the required Python packages.

4. **Run the Application**:

    After setting up the environment, you can run the application with the following command:

    ```bash
    python3 app.py
    ```

    The service will start, and it will be ready to accept connections from the frontend.

## Getting Started, (Docker deployment)

Have docker and docker compose installed on your system. Run "docker compose up backend --build" to start the service in a dev mode. Your container will hot reload on a save to the code as you edit. Connect to this container with a vite service in /frontend. On deployment for production run docker compose up --build in the root directory and a small service will host the frontend files on localhost:3000.
