const express = require('express');
const fs = require('fs').promises;
const path = require('path');
const cors = require('cors');
const pdfParse = require('pdf-parse');

const app = express();
const PORT = 3000;

// Middleware
app.use(cors());
app.use(express.json());

// Sample files are in backend/sample
const BACKEND_DIR = path.join(__dirname, 'sample');

// API endpoint to read file (supports .txt and .pdf)
app.get('/api/read-file', async (req, res) => {
    try {
        const filename = req.query.filename;

        if (!filename) {
            return res.status(400).json({ error: 'Filename is required' });
        }

        // Sanitize filename to prevent directory traversal
        const sanitizedFilename = path.basename(filename);
        const filePath = path.join(BACKEND_DIR, sanitizedFilename);
        const ext = path.extname(sanitizedFilename).toLowerCase();

        try {
            let text;

            if (ext === '.pdf') {
                // Read PDF as buffer and extract text
                const dataBuffer = await fs.readFile(filePath);
                const pdfData = await pdfParse(dataBuffer);
                text = pdfData.text;
                if (!text || !text.trim()) {
                    text = '(No extractable text in this PDF.)';
                }
            } else if (ext === '.txt' || ext === '') {
                // Read text file as UTF-8
                text = await fs.readFile(filePath, 'utf-8');
            } else {
                return res.status(400).json({
                    error: `Unsupported file type "${ext}". Use .txt or .pdf`
                });
            }

            res.json({
                success: true,
                filename: sanitizedFilename,
                content: text
            });
        } catch (error) {
            if (error.code === 'ENOENT') {
                res.status(404).json({
                    error: `File "${sanitizedFilename}" not found`
                });
            } else {
                throw error;
            }
        }
    } catch (error) {
        console.error('Error reading file:', error);
        res.status(500).json({
            error: 'Internal server error'
        });
    }
});

// Health check endpoint
app.get('/api/health', (req, res) => {
    res.json({ status: 'ok' });
});

app.listen(PORT, () => {
    console.log(`Server is running on http://localhost:${PORT}`);
    console.log(`Backend directory: ${BACKEND_DIR}`);
});
