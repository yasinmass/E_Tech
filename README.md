# 🏗️ E-Tech Builders – Construction Management System

A web-based construction management system built using Django that helps manage workers, attendance, site updates, and bill tracking in a simple and efficient way.

---

## 🚀 Features

### 👷 Worker Management
- Add, edit, and delete workers
- View worker details and status
- Track worker activity history

### 🗓️ Attendance System
- Admin-based attendance marking
- Centralized and controlled system
- Avoids duplicate or incorrect entries

### 🧾 Bill Management
- Upload bill images
- Store and manage expense records
- View and track bills per site

### 📍 Site Management
- Create and manage multiple construction sites
- Assign workers to sites
- Track site-specific updates

### 📝 Work Updates
- Workers can submit daily updates
- Admin can review all updates
- Maintains transparency across projects

### 📊 Activity History
- Logs all important actions
- Tracks user activity across the app

---

## 🛠️ Tech Stack

- **Backend:** Django (Python)
- **Frontend:** HTML, CSS, JavaScript
- **Database:** SQLite (for development)
- **Hosting:** PythonAnywhere
- **Media Storage:** Local / Cloudinary (optional)

---

## ⚙️ Installation (Local Setup)

```bash
# Clone the repository
git clone https://github.com/yasinmass/E_Tech.git

# Navigate into project
cd E_Tech

# Create virtual environment
python -m venv venv

# Activate environment
source venv/bin/activate  # Linux
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Start server
python manage.py runserver
