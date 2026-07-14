# AI-Driven Public Health Chatbot

An intelligent, AI-powered public health assistant designed to provide clear, accurate, and compassionate health information. The application features a modern React frontend and a robust Python Flask backend utilizing Google's Gemini AI and SQLite for a seamless user experience.

## 🌟 Features
- **AI Chatbot**: Powered by Gemini 1.5 Flash (with offline keyword fallback) to answer health queries, provide symptom guidance, and give first aid instructions.
- **Multi-language Support**: Automatically translates user messages and AI responses using `deep-translator`.
- **Health Dashboard**: Displays the latest health alerts, disease outbreaks, and preventive measures.
- **Disease & Vaccine Info**: Access a comprehensive database of common diseases, their symptoms, prevention methods, and recommended vaccines.
- **User Authentication**: Secure login and registration system with password hashing.
- **Zero Configuration DB**: Uses SQLite, meaning the database automatically sets itself up on the first run.

## 🛠️ Tech Stack
- **Frontend**: React 19, Vite, Tailwind CSS v4, Lucide React (Icons)
- **Backend**: Python, Flask, SQLite3, Google Generative AI (Gemini), Werkzeug
- **Other Tools**: deep-translator, python-dotenv

## 🚀 Getting Started

### Prerequisites
- Node.js (for the frontend)
- Python 3.x (for the backend)
- Gemini API Key (Optional, but recommended for AI features)

### 1. Setup the Backend
1. Navigate to the `backend` directory (if you are running it separately) or stay in the root and run the app.py directly.
2. Install the required Python packages:
   ```bash
   pip install flask werkzeug deep-translator python-dotenv google-generativeai
   ```
3. Create a `.env` file in the same directory as `app.py` and add your Gemini API key:
   ```env
   GEMINI_API_KEY=your_api_key_here
   ```
4. Run the Flask server:
   ```bash
   python backend/app.py
   ```
   The backend will start at `http://localhost:5000`.

### 2. Setup the Frontend
1. Open a new terminal and navigate to the project root directory.
2. Install the Node dependencies:
   ```bash
   npm install
   ```
3. Start the Vite development server:
   ```bash
   npm run dev
   ```
4. Open the provided `localhost` URL in your browser to view the React app!

## ⚠️ Disclaimer
This chatbot provides general health information and is **not** a substitute for professional medical advice, diagnosis, or treatment. Always seek the advice of your physician or other qualified health provider with any questions you may have regarding a medical condition.
