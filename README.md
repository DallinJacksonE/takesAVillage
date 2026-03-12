# Takes a Village

Takes a Village is a multiplayer social dilemma game about specialization, societies, and survival. Players must gather resources, build a community, and navigate complex social interactions to thrive.

## Game Overview

Welcome to the Village. You spawn in an undeveloped area with raw resources. Your goal is to survive the longest and build the most prosperous village. To do this, you must manage your resources, your developments, and your social relationships with other players.

Each day in the game is divided into three distinct phases:

### 1. Work Phase

This is the production phase. Players can:

- **Gather Resources:** Work at developments to produce essential resources like food and wood.
- **Build & Upgrade:** Construct new developments on the map or upgrade existing ones to increase their output.
- **Offer Employment:** Hire other players to work at your developments in exchange for wages.
- **Initiate Conflict:** Attempt to seize a development from another player, leading to a multi-day conflict that other players can join.

### 2. Trade Phase

This phase is all about negotiation and exchange. Players can:

- **Pay Employees:** Employers distribute wages to players who worked for them. However, employers can choose to pay less than what was agreed upon, introducing an element of deception.
- **Trade Resources:** Freely trade resources with other players. Similar to employment, players can lie during a trade, promising one set of items but sending another.
- **Barter:** Negotiate the terms of employment offers and trades.

### 3. Night Phase

The survival phase. At the end of each day, players must:

- **Eat:** Consume one unit of food. Failing to eat will impact your health.
- **Stay Warm:** Consume one unit of wood to build a fire. Players can invite others to share their fire, saving resources. Failing to stay warm increases the chance of sickness, which prevents you from working the next day.

## Technical Overview

This project is composed of two main parts:

- **Frontend**: A React application built with TypeScript that serves as the game client. It uses a Model-View-Presenter (MVP) architecture for a clean separation of concerns.
- **Backend**: A Python server using Flask and Flask-SocketIO to manage game logic, real-time communication, and data persistence with a MySQL database.

## Getting Started

To run the project, you will need to set up both the frontend and the backend services. Detailed instructions for each part can be found in their respective directories:

- **For the frontend application, see: [`frontend/README.md`](/frontend/README.md)**
- **For the backend service, see: `service/README.md`**
