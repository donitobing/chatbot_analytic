# ChatBot Analytic

Created by: **Doni Tobing**

A modern web application that allows users to upload documents (Word, Excel, PDF, Text) and chat with their documents using OpenAI's powerful AI capabilities.

## Features

- **Document Upload**: Upload various document formats (Word, Excel, PDF, Text) for AI analysis
- **AI-Powered Chatbot**: Ask questions about your uploaded documents and get detailed answers
- **Modern Web UI**: Clean, responsive design with drag-and-drop file uploads
- **Multi-format Support**: Process and analyze various document formats


## Tech Stack

- **Backend**: Python, Flask
- **Frontend**: HTML, CSS, JavaScript
- **AI Integration**: OpenAI API
- **Document Processing**: LangChain, pandas, python-docx, pdfplumber

## Installation

1. Clone the repository:
```bash
git clone https://github.com/donitobing/chatbot_analytic.git
cd ChatBotAnalytic
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file in the root directory with your OpenAI API key:
```
OPENAI_API_KEY=your_openai_api_key_here
```

## Usage

1. Start the application:
```bash
python app.py
```

2. Open your web browser and navigate to:
```
http://127.0.0.1:5000/
```

3. Upload documents using the sidebar drag-and-drop interface
4. Chat with your documents in the main chat window

## Project Structure

```
ChatBotAnalytic/
├── app.py                  # Main Flask application
├── chatbot.py              # OpenAI integration for Q&A
├── document_processor.py   # Document processing and storage
├── requirements.txt        # Python dependencies
├── .env                    # Environment variables (OpenAI API key)
├── static/                 # Static files
│   ├── css/
│   │   └── style.css       # Application styling
│   └── js/
│       └── main.js         # Frontend JavaScript
├── templates/              # HTML templates
│   └── index.html          # Main application page
└── uploads/                # Directory for uploaded files
```

## Supported File Types

- Word Documents (.docx)
- Excel Spreadsheets (.xlsx, .xls)
- PDF Files (.pdf)
- Text Files (.txt)

## Development

### Prerequisites

- Python 3.7+
- OpenAI API Key

### Local Development

1. Clone the repository
2. Set up a virtual environment (recommended)
3. Install dependencies
4. Create `.env` file with your OpenAI API key
5. Run the application

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is free for contribution and use by the community. You are welcome to modify, distribute, and use it for both personal and commercial purposes without restrictions. No formal license file is required - feel free to contribute, share and improve this project.

## Acknowledgements

- [OpenAI](https://openai.com/) for providing the AI capabilities
- [Flask](https://flask.palletsprojects.com/) for the web framework
- [LangChain](https://github.com/langchain-ai/langchain) for document processing
