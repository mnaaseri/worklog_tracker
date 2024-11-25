# Worklog Tracker

Worklog Tracker is a personal worklog management application that utilizes a Django backend and integrates with a Telegram bot for seamless interaction. This project aims to help users efficiently track and manage their daily work activities.

## Features

- **Django Backend**: Robust and scalable backend built with Django.
- **Telegram Bot Integration**: Interact with the worklog tracker via a Telegram bot.
- **User Authentication**: Secure login and registration system.
- **Worklog Management**: Create, update, and delete worklog entries.
- **Reporting**: Generate reports of worklogs over specified periods.

## Installation

### Prerequisites

- Docker
- Docker Compose

### Setup with Docker Compose

1. **Clone the repository:**

   ```bash
   git clone https://github.com/yourusername/worklog_tracker.git
   cd worklog_tracker
   ```

2. **Create an `.env` file:**

   Create a `.env` file in the root directory with the necessary environment variables, such as database credentials and the Telegram bot token.

3. **Build and run the containers:**

   ```bash
   docker-compose up --build
   ```

   This command will build the Docker images and start the services defined in the `docker-compose.yml` file.

4. **Access the application:**

   - The Django application will be available at `http://localhost:8000`.
   - Use the Telegram bot to interact with your worklog by sending commands.


## Use Cases

### Worklog Management

#### Log Work Hours
- **Description**: Log work hours and days.
- **Preconditions**: Must be logged into the system.

#### Review Worklog
- **Description**: Get worklog entries by day or month.
- **Preconditions**: Must be logged into the system.


#### Log Leave Hours
- **Description**: Add leave hour or days.
- **Preconditions**: Must be logged into the system.


#### Review Leave
- **Description**: Get leave hour or days by day or month.
- **Preconditions**:  Must be logged into the system.

### Telegram Integration

#### Add Worklog or Leave Hours
- **Description**: Add time of starting and ending a work or leave via Telegram bot.
- **Preconditions**: Must use a telegram account with the same id used when siging up. 

#### Get Worklog or Leave Hours
- **Description**: Get total work or leave hours via Telegram bot.
- **Preconditions**: Must use a telegram account with the same id used when siging up. 

#### Sign up
- **Description**: Sign up to add or get worklog or leave times. 


