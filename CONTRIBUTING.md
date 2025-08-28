# Contributing to Google Voice REST API

## Getting Started

1. Fork the repository
2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Copy `.env.example` to `.env` and configure

## Development Setup

Run in development mode:
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Code Style

- Follow PEP 8
- Use type hints where applicable
- Add docstrings to all functions/classes
- Keep lines under 100 characters

## Testing

Run tests:
```bash
pytest
```

## Pull Request Process

1. Create a new branch: `git checkout -b feature/your-feature-name`
2. Make your changes
3. Add tests for new functionality
4. Ensure all tests pass
5. Update documentation if needed
6. Submit a pull request

## Areas for Contribution

- Browser automation for cookie extraction (see issue #1)
- Protobuf parsing implementation
- Real-time message receiving
- Voice call support
- Better error handling
- Additional authentication methods
- Unit tests
- Integration tests

## Security

- Never commit actual Google cookies or sessions
- Keep authentication tokens secure
- Report security issues privately