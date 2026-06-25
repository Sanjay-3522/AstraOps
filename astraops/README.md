# 🚦 AstraOps — Event Response Intelligence System

### AI-Powered Traffic Incident Prediction & Response Planning

AstraOps is an intelligent decision-support platform designed to help traffic authorities anticipate, assess, and respond to planned and unplanned traffic disruptions. By analyzing historical traffic incident data from Bengaluru's Astram dataset, the system predicts potential traffic impact and generates actionable response plans for faster, safer, and more efficient traffic management.

---

## 🎯 Problem Statement

Traffic disruptions caused by accidents, public events, VIP movements, protests, road works, and environmental incidents often lead to severe congestion and delayed emergency response.

Current traffic management workflows rely heavily on manual assessment, making it difficult to:

* Estimate the severity of an incident
* Predict road closure requirements
* Allocate resources efficiently
* Plan diversions proactively
* Learn from past incidents

AstraOps addresses these challenges through data-driven intelligence and automated response recommendations.

---

## 💡 Solution

AstraOps transforms historical incident records into operational intelligence.

For any incoming traffic event, the platform can:

* Predict traffic impact severity
* Estimate road closure probability
* Forecast incident clearance time
* Recommend manpower deployment
* Suggest barricading requirements
* Generate diversion strategies
* Retrieve similar historical incidents
* Record outcomes for continuous improvement

This enables authorities to move from reactive traffic management to proactive decision-making.

---

## 🚀 Key Features

### 📊 Impact Prediction

Evaluates the expected traffic impact of an event using historical incident patterns and contextual information.

### 🚧 Road Closure Assessment

Predicts whether an incident is likely to require partial or complete road closure.

### ⏱️ Clearance Time Estimation

Forecasts how long it may take to resolve an incident and restore normal traffic flow.

### 👮 Resource Recommendation Engine

Provides recommendations for manpower deployment, barricades, and traffic control measures.

### 🗺️ Diversion Planning

Suggests traffic diversion strategies to minimize congestion during disruptions.

### 🔍 Similar Incident Analysis

Identifies historical incidents with comparable characteristics and displays their outcomes.

### 📚 Learning Log

Captures predicted and actual outcomes, enabling performance evaluation and future model improvement.

### 🎛️ Planning Simulator

Allows operators to simulate hypothetical incidents and evaluate response strategies before deployment.

---

## 🏗️ System Workflow

```text
Traffic Event
      │
      ▼
Feature Engineering
      │
      ▼
Prediction Engine
      │
 ┌────┼────┬─────┐
 ▼    ▼    ▼     ▼
Impact Closure ETA Resources
      │
      ▼
Recommendation Engine
      │
      ▼
Operator Dashboard
      │
      ▼
Feedback & Learning
```

---

## 📂 Project Architecture

```text
AstraOps
│
├── Frontend (React + Vite)
│   │
│   ├── Dashboard
│   ├── Live Incident Map
│   ├── Event Detail View
│   ├── Planning Simulator
│   ├── Learning Log
│   └── Reusable UI Components
│
├── Backend (Flask REST API)
│   │
│   ├── Data Cleaning Pipeline
│   ├── Feature Engineering
│   ├── Closure Prediction Model
│   ├── Clearance ETA Prediction Model
│   ├── Recommendation Engine
│   ├── Similar Incident Retrieval
│   ├── Feedback & Learning System
│   └── API Layer
│
├── Model Storage
│   ├── Trained Classifier
│   ├── Trained Regressor
│   └── Metrics & Artifacts
│
├── Processed Incident Data
│
└── Historical Astram Dataset
```

---

## 📈 Model Performance

### Closure Prediction

* ROC-AUC: 0.78
* PR-AUC: 0.38
* Recall: 52%

### Clearance Time Prediction

* Mean Absolute Error: 1.25 Hours
* Median Absolute Error: 0.49 Hours

Performance metrics are generated automatically during model training.

---

## 🛠️ Technology Stack

### Frontend

* React
* Vite
* JavaScript
* Tailwind CSS

### Backend

* Flask
* REST APIs

### Machine Learning

* Scikit-learn
* HistGradientBoosting Classifier
* HistGradientBoosting Regressor

### Data Processing

* Pandas
* NumPy

### Storage

* JSON-based Feedback Logging

---

## 🌍 Impact

AstraOps empowers traffic management authorities with actionable intelligence for incident response planning.

By combining predictive analytics, recommendation systems, and historical incident learning, the platform helps:

* Reduce traffic congestion
* Improve response efficiency
* Optimize resource allocation
* Support data-driven decision making
* Enhance urban mobility

---

## 🔮 Future Enhancements

* Real-time traffic data integration
* GIS-based traffic visualization
* Congestion forecasting
* Automated dispatch recommendations
* Multi-city deployment support
* Continuous model retraining from live feedback

---

## 👨‍💻 Team

Built as an AI-powered Event Response Intelligence System for smarter and more resilient urban traffic management.

### Transforming Historical Traffic Data into Real-Time Operational Intelligence.
