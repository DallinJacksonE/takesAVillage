# Takes a Village - Frontend

This is the frontend for the "Takes a Village" project. It is a React application built with TypeScript and Vite.

## Tech Stack

*   **[React](https://react.dev/)**: A JavaScript library for building user interfaces.
*   **[TypeScript](https://www.typescriptlang.org/)**: A typed superset of JavaScript that compiles to plain JavaScript.
*   **[Vite](https://vitejs.dev/)**: A build tool that aims to provide a faster and leaner development experience for modern web projects.
*   **[React Router](https://reactrouter.com/)**: For declarative routing in the application.
*   **[Socket.IO Client](https://socket.io/docs/v4/client-api/)**: For real-time communication with the backend service.

## Architecture - Model-View-Presenter (MVP)

This project is structured using the **Model-View-Presenter (MVP)** architectural pattern. MVP is a derivative of the Model-View-Controller (MVC) pattern, but with a few key differences that can make it more suitable for complex user interfaces.

### What is MVP?

MVP is an architectural pattern that separates the concerns of an application into three interconnected components:

*   **Model**: The Model is responsible for the application's data and business logic. It has no direct knowledge of the user interface. In this project, the `service` directory contains the code that interacts with the backend API, acting as our Model. It fetches and pushes data to and from the server.

*   **View**: The View is a passive interface that displays data (the model) and routes user commands (events) to the Presenter to act upon that data. The View is responsible for the "look and feel" of the application. In our React application, the components in the `views` directory are the primary Views. They are responsible for rendering the UI and passing user interactions to the Presenter.

*   **Presenter**: The Presenter acts as the "middle-man" between the Model and the View. It retrieves data from the Model and formats it for display in the View. It also reacts to user input from the View and updates the Model. The Presenter is the main hub of user interaction logic. Our `presenters` directory contains these classes.

### Why MVP?

*   **Separation of Concerns**: MVP provides a clean separation between the user interface (View) and the application's logic (Presenter) and data (Model). This makes the code easier to understand, maintain, and test.
*   **Testability**: Because the Presenter is decoupled from the View, we can write unit tests for the Presenter and Model without needing to interact with the UI. This makes our tests faster and more reliable.
*   **Flexibility**: With MVP, the same Presenter and Model can be used with different Views, allowing for easier UI changes without affecting the underlying business logic.

## Project Structure

```
frontend/
├── src/
│   ├── assets/         # Static assets like images and fonts
│   ├── components/     # Reusable React components used across multiple views
│   ├── presenters/     # Presenter classes that contain UI logic
│   ├── service/        # Services that interact with the backend API (our Model)
│   ├── types/          # TypeScript type definitions
│   └── views/          # Top-level view components (the "pages" of the app)
├── vite.config.ts    # Vite configuration
├── tsconfig.json     # TypeScript configuration
└── package.json      # Project dependencies and scripts
```

### Directory Breakdown

*   `src/assets`: Static files like images, SVGs, and fonts.
*   `src/components`: Smaller, reusable React components that can be composed to build complex UIs. For example, a `Button` or a `Modal` component.
*   `src/presenters`: These classes are the core of the MVP architecture. They handle the logic of what to display and how to react to user input. Each major view or component with complex state will have a corresponding Presenter.
*   `src/service`: This directory acts as the Model layer. It contains services that are responsible for making API calls to the backend and managing the data.
*   `src/types`: Contains all TypeScript type definitions, interfaces, and enums. This helps in maintaining a consistent data structure across the application.
*   `src/views`: These are the main "pages" of the application, like the Home page, Dashboard, etc. They are composed of smaller components and are managed by their corresponding Presenters.

## Getting Started

1.  **Install Dependencies**:
    ```bash
    npm install
    ```

2.  **Run the Development Server**:
    ```bash
    npm run dev
    ```
    This will start the Vite development server, and you can view the application at `http://localhost:5173`.

3.  **Build for Production**:
    ```bash
    npm run build
    ```
    This will create a `dist` directory with the production-ready build of the application.
