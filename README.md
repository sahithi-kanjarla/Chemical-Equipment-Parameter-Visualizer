# Chemical Equipment Parameter Visualizer

A full-stack application for analyzing chemical equipment datasets through a **React web application** and a **PyQt5 desktop application**, powered by a shared Django REST API and SQLite database.

Upload engineering data, explore equipment parameters through visualizations, analyze statistical summaries, and generate downloadable PDF reports.

## Application Preview

### Web Application

![Web Application](https://github.com/user-attachments/assets/c2235a52-8dd5-4a3d-9165-1f1b8700c8ea)

### Data Visualization

![Data Visualization](https://github.com/user-attachments/assets/9d76f208-7c9d-4750-af75-f5a93ee45df4)

![Data Visualization](https://github.com/user-attachments/assets/8bd5e7e2-6885-4be5-b6c6-eb7ec854bad5)

### Desktop Application

![Desktop Application](https://github.com/user-attachments/assets/bb096180-39a7-4043-9f87-8eab0f41be9a)

---

## Overview

The application allows users to upload engineering datasets in CSV format, analyze chemical equipment parameters, visualize statistical results, and generate PDF reports.

It provides two client interfaces:

- **Web Application:** A responsive React interface with interactive charts and data exploration.
- **Desktop Application:** A PyQt5 interface with Matplotlib-based data visualization.

Both applications communicate with a shared Django REST API for centralized data processing, authentication, and dataset management.

## Key Features

- CSV upload with data validation.
- Automated statistical analysis using Pandas.
- Equipment-type analysis and summary statistics.
- Interactive charts and data visualization.
- Separate web and desktop interfaces.
- JWT-based authentication and user-specific upload history.
- Per-user data isolation.
- Downloadable PDF reports.

## Technology Stack

| Component | Technologies |
|---|---|
| Web Frontend | React, JavaScript, CSS, Chart.js |
| Backend | Python, Django, Django REST Framework |
| Desktop | PyQt5, Matplotlib |
| Data Processing | Pandas |
| Database | SQLite |
| Authentication | JWT |

---

## Architecture

Both client applications communicate with a shared Django REST API, which handles authentication, CSV validation, data processing, and storage.

```text
                  ┌──────────────────────┐
                  │        Users         │
                  └──────────┬───────────┘
                             │
                 ┌───────────┴───────────┐
                 │                       │
                 ▼                       ▼
          React Web App            PyQt5 Desktop
                 │                       │
                 └───────────┬───────────┘
                             │
                             ▼
                   Django REST API
                             │
                 ┌───────────┴───────────┐
                 │                       │
                 ▼                       ▼
             SQLite DB                Pandas
                                         │
                                         ▼
                                  Data Analysis
                                         │
                                         ▼
                                    PDF Reports
```

## System Workflow

1. Users authenticate through JWT.
2. Users upload engineering datasets through either application.
3. The backend validates the CSV files.
4. Pandas processes the uploaded dataset.
5. Statistical metrics and equipment distributions are calculated.
6. Datasets are associated with the authenticated user.
7. Results are visualized using Chart.js or Matplotlib.
8. Users can generate downloadable PDF reports.

### Analysis Metrics

- Total record count
- Average flowrate
- Average pressure
- Average temperature
- Equipment type distribution
- Per-type parameter averages
- Dataset preview

---

## Supported Dataset Format

The uploaded CSV file must contain:

```text
Equipment Name
Type
Flowrate
Pressure
Temperature
```

---

## Project Structure

```text
chemical-visualizer/
│
├── api/
│   ├── models.py
│   ├── views.py
│   ├── serializers.py
│   └── urls.py
│
├── project/
│   ├── settings.py
│   └── urls.py
│
├── manage.py
│
├── web-frontend/
│   ├── src/
│   └── package.json
│
└── desktop-frontend/
    ├── pyqt_app.py
    └── api_client.py
```

---

## Getting Started

### Prerequisites

- Python 3.x
- Node.js
- npm

### 1. Clone the Repository

```bash
git clone https://github.com/sahithi-kanjarla/Chemical-Equipment-Parameter-Visualizer.git
cd Chemical-Equipment-Parameter-Visualizer
```

### 2. Set Up the Backend

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

Install dependencies:

```bash
pip install -r requirements.txt
```

Run migrations and create an admin account:

```bash
python manage.py migrate
python manage.py createsuperuser
```

Start the backend:

```bash
python manage.py runserver
```

### 3. Run the Web Application

```bash
cd web-frontend
npm install
npm start
```

Available at `http://localhost:3000/`.

### 4. Run the Desktop Application

Activate the Python virtual environment:

```bash
pip install pyqt5 matplotlib requests
cd desktop-frontend
python pyqt_app.py
```

---

