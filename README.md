# Voice File Reader Frontend

A web application that uses voice recognition to read text files from the backend.

## Features

- 🎤 Voice input using Web Speech API
- 📄 Reads text files from the backend folder
- ❌ Shows error message when file is not found
- 🎨 Modern, responsive UI

## Setup

1. Install backend dependencies:

   ```bash
   cd backend
   npm install
   ```

2. Start the backend server:

   ```bash
   npm start
   ```

3. Open `index.html` in a web browser (Chrome or Edge recommended for best speech recognition support)

## Usage

1. Click "Start Voice Input" button
2. Speak the filename (e.g., "hello.txt" or "read hello.txt")
3. The application will fetch and display the file content
4. If the file doesn't exist, an error message will be shown

## Browser Compatibility

- Chrome/Edge: Full support
- Firefox: Limited support
- Safari: Limited support

## API Endpoint

The frontend communicates with the backend API:

- `GET /api/read-file?filename=<filename>` - Reads a file from the backend folder
