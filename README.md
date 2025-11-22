# Chemical Equipment Parameter Visualizer  
A hybrid application that allows users to upload engineering datasets in CSV format and visualize analytics through a **React Web Application**, a **PyQt5 Desktop Application**, and a shared **Django REST API Backend**.

---

## 🚀 How It Works (Project Flow)
1. User logs in using their account (JWT authentication)
2. User uploads a CSV file (via Web or Desktop)
3. Django backend reads CSV using Pandas
4. Backend computes:
   - total_count  
   - averages (Flowrate, Pressure, Temperature)  
   - type_distribution  
   - per-type averages  
   - preview_rows  
5. File is stored and linked to the AUTHENTICATED user
6. Each user sees only **their last 5 uploads** (History)
7. Web shows responsive charts using Chart.js
8. Desktop displays offline charts using Matplotlib
9. User can **generate PDF reports** from summary or stored dataset

---

## 📁 Project Structure
```
chemical-visualizer/
│
├── api/                     # Django API
│   ├── models.py
│   ├── views.py
│   ├── serializers.py
│   ├── urls.py
│
├── project/                 # Django Project Settings
│   ├── settings.py
│   ├── urls.py
│
├── manage.py                # Backend entry point
│
├── web-frontend/            # React Web App
│   ├── src/
│   │   ├── components/
│   │   ├── styles/
│   │   ├── api.js
│   │   ├── App.js
│   ├── package.json
│
└── desktop-frontend/        # PyQt Desktop App
    ├── pyqt_app.py
    ├── api_client.py
```

---

# ⚙️ Backend Setup (Django REST API)

### 1️⃣ Create Virtual Environment  
Windows:
```bash
python -m venv venv
venv\Scripts\activate
```
Mac/Linux:
```bash
python3 -m venv venv
source venv/bin/activate
```

### 2️⃣ Install Required Packages
```bash
pip install -r requirements.txt
```

### 3️⃣ Run Database Migrations
```bash
python manage.py migrate
```

### 4️⃣ Create Admin / User accounts
```bash
python manage.py createsuperuser
```

### 5️⃣ Start Django Backend Server (Terminal 1)
```bash
python manage.py runserver
```

> Keep this terminal running — backend must be active for frontend and desktop apps.

---

# 🌐 Web Frontend Setup (React)

### Open a **new terminal** (Terminal 2)
> Do NOT activate virtual environment here (if active, run `deactivate`)

```bash
cd web-frontend
npm install
npm start
```

Runs automatically at:
```
http://localhost:3000/
```

📱 Fully responsive on desktop & mobile

<img width="1357" height="576" alt="image" src="https://github.com/user-attachments/assets/c2235a52-8dd5-4a3d-9165-1f1b8700c8ea" />

---<img width="1355" height="577" alt="Screenshot 2025-11-23 023336" src="https://github.com/user-attachments/assets/9d76f208-7c9d-4750-af75-f5a93ee45df4" />

<img width="1358" height="578" alt="Screenshot 2025-11-23 023541" src="https://github.com/user-attachments/assets/8bd5e7e2-6885-4be5-b6c6-eb7ec854bad5" />

# 🖥 Desktop App Setup (PyQt5)


### Open another **new terminal** (Terminal 3)
> venv MUST be activated
```bash
venv\Scripts\activate          # Windows
source venv/bin/activate       # Mac/Linux
```

### Install dependencies
```bash
pip install pyqt5 matplotlib requests
```

### Run desktop app
```bash
cd desktop-frontend
python pyqt_app.py
```

---
<img width="1365" height="717" alt="image" src="https://github.com/user-attachments/assets/bb096180-39a7-4043-9f87-8eab0f41be9a" />


# ✨ Application Features

## ✔ CSV Upload (with validation)
Required columns:
- Equipment Name
- Type
- Flowrate
- Pressure
- Temperature

## ✔ Data Analysis & Computation
- Summary statistics
- Per-type averages
- Missing values
- Preview rows

## ✔ Chart Visualization
Web App (Chart.js):
- Bar, Pie, Line, Histogram
- Change chart type per parameter
- Remove/restore charts
- Smooth responsive layout

Desktop App (Matplotlib):
- Offline plotting

## ✔ User-Specific Upload History
- Stores **last 5 uploads per user**
- Clicking an item loads dataset instantly
- Data isolation per user

## ✔ PDF Report Generation
- Summary + charts + preview table
- Downloadable
- Works on saved datasets & live analysis

---

# 📦 Final Project Summary
| Feature | Status |
|--------|--------|
| User Login & JWT Auth | ✔ Done |
| CSV Upload & Validation | ✔ Done |
| Summary + Graphs | ✔ Done |
| User-based Upload History | ✔ Done |
| Responsive Web UI | ✔ Done |
| Desktop Client | ✔ Done |
| PDF Report | ✔ Done |
| Per-user isolation | ✔ Done |

---




