# Chemical Equipment Parameter Visualizer

A full-stack data visualization application for analyzing chemical equipment datasets through a **React web application** and **PyQt5 desktop application**, powered by a shared **Django REST API** and **SQLite database**.

## Tech Stack

**Frontend:** React, JavaScript, CSS, Chart.js
**Backend:** Django, Django REST Framework
**Desktop:** PyQt5, Matplotlib
**Data Processing:** Python, Pandas
**Database:** SQLite
**Authentication:** JWT

---

## Overview

The Chemical Equipment Parameter Visualizer allows users to upload engineering datasets in CSV format, analyze equipment parameters, visualize the results, and generate downloadable PDF reports.

The application provides two client interfaces — a responsive React web application and a PyQt5 desktop application — connected to a shared Django REST API backend.

---

## Key Features

* CSV upload with validation
* Automated data analysis using Pandas
* Summary statistics and per-type analysis
* Interactive data visualization with Chart.js
* Offline visualization with Matplotlib
* JWT-based authentication
* User-specific upload history
* Per-user data isolation
* PDF report generation
* Web and desktop clients using a shared REST API

---

## Application Preview

### Web Application

![Web Application](https://github.com/user-attachments/assets/c2235a52-8dd5-4a3d-9165-1f1b8700c8ea)

### Data Visualization

![Data Visualization](https://github.com/user-attachments/assets/9d76f208-7c9d-4750-af75-f5a93ee45df4)

![Data Visualization](https://github.com/user-attachments/assets/8bd5e7e2-6885-4be5-b6c6-eb7ec854bad5)

### Desktop Application

![Desktop Application](https://github.com/user-attachments/assets/bb096180-39a7-4043-9f87-8eab0f41be9a)

---

## System Workflow

```text
User
 │
 ▼
JWT Authentication
 │
 ▼
CSV Upload
 │
 ▼
Django REST API
 │
 ├── CSV Validation
 ├── Pandas Data Processing
 ├── Statistical Analysis
 └── User-specific Data Storage
 │
 ├───────────────────┐
 ▼                   ▼
React Web App     PyQt5 Desktop App
 │                   │
Chart.js           Matplotlib
 │                   │
 └─────────┬─────────┘
           ▼
      PDF Reports
```

### Processing Flow

1. User authenticates using JWT authentication.
2. User uploads a CSV file through the web or desktop application.
3. The Django backend validates and processes the dataset using Pandas.
4. The backend calculates:

   * Total record count
   * Average flowrate
   * Average pressure
   * Average temperature
   * Equipment type distribution
   * Per-type averages
   * Dataset preview
5. The uploaded dataset is associated with the authenticated user.
6. Each user can access their last five uploaded datasets.
7. The web application visualizes the processed data using Chart.js.
8. The desktop application provides offline visualization using Matplotlib.
9. Users can generate PDF reports from analyzed or stored datasets.

---

## Supported Dataset Format

The uploaded CSV file must contain the following columns:

```text
Equipment Name
Type
Flowrate
Pressure
Temperature
```

---

## Application Features

### CSV Upload & Validation

The application validates uploaded CSV files and checks for the required equipment and parameter columns.

### Data Analysis

Uploaded datasets are processed using Pandas to generate:

* Summary statistics
* Per-type averages
* Missing-value information
* Dataset preview
* Equipment type distribution

### Data Visualization

**Web Application — Chart.js**

* Bar charts
* Pie charts
* Line charts
* Histograms
* Parameter-based chart selection
* Chart removal and restoration
* Responsive layout

**Desktop Application — Matplotlib**

* Offline data visualization

### User-Specific Upload History

* Stores the last five uploads for each user
* Previously uploaded datasets can be loaded from history
* User data is isolated through authenticated access

### PDF Report Generation

Users can generate downloadable reports containing:

* Dataset summary
* Charts
* Preview tables
* Analysis results

Reports can be generated from both newly analyzed and previously stored datasets.

---

## Project Structure

```text
chemical-visualizer/
│
├── api/                         # Django REST API
│   ├── models.py
│   ├── views.py
│   ├── serializers.py
│   └── urls.py
│
├── project/                     # Django project configuration
│   ├── settings.py
│   └── urls.py
│
├── manage.py                    # Django entry point
│
├── web-frontend/                # React web application
│   ├── src/
│   │   ├── components/
│   │   ├── styles/
│   │   ├── api.js
│   │   └── App.js
│   └── package.json
│
└── desktop-frontend/            # PyQt5 desktop application
    ├── pyqt_app.py
    └── api_client.py
```

---

## Getting Started

### Prerequisites

Make sure the following are installed:

* Python 3.x
* Node.js
* npm

### 1. Clone the Repository

```bash
git clone https://github.com/sahithi-kanjarla/Chemical-Equipment-Parameter-Visualizer.git
cd Chemical-Equipment-Parameter-Visualizer
```

### 2. Set Up the Backend

Create and activate a Python virtual environment.

**Windows**

```bash
python -m venv venv
venv\Scripts\activate
```

**macOS / Linux**

```bash
python3 -m venv venv
source venv/bin/activate
```

Install the backend dependencies:

```bash
pip install -r requirements.txt
```

Run database migrations:

```bash
python manage.py migrate
```

Create an admin account:

```bash
python manage.py createsuperuser
```

Start the Django development server:

```bash
python manage.py runserver
```

Keep the backend server running while using the web or desktop application.

### 3. Run the Web Application

Open a new terminal and navigate to the web application:

```bash
cd web-frontend
npm install
npm start
```

The application will be available at:

```text
http://localhost:3000/
```

### 4. Run the Desktop Application

Activate the Python virtual environment and install the desktop dependencies:

```bash
pip install pyqt5 matplotlib requests
```

Then run:

```bash
cd desktop-frontend
python pyqt_app.py
```

---

## Architecture

The application follows a shared-backend architecture where both client applications communicate with the same Django REST API.

```text
                    ┌────────────────────┐
                    │       Users        │
                    └─────────┬──────────┘
                              │
                 ┌────────────┴────────────┐
                 │                         │
                 ▼                         ▼
          React Web App             PyQt5 Desktop
                 │                         │
                 └────────────┬────────────┘
                              │
                              ▼
                    Django REST API
                              │
                 ┌────────────┴────────────┐
                 │                         │
                 ▼                         ▼
             SQLite DB                  Pandas
                                           │
                                           ▼
                                    Data Analysis
```




