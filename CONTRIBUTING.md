# Contributing to RAG-API

Thank you for your interest in contributing! Here's how to get started.

## Getting Started

1. **Fork** the repository and clone your fork.
2. Create a **virtual environment** and install dev dependencies:
   ```bash
   python -m venv venv
   source venv/bin/activate   # or venv\Scripts\activate on Windows
   pip install -r requirements-dev.txt
   ```
3. Make sure **Ollama** is installed if you want to test with a real LLM, or use `USE_MOCK_LLM=1` for testing without one.

## Development Workflow

1. Create a feature branch: `git checkout -b feature/your-feature`
2. Make your changes.
3. Run the test suite:
   ```bash
   pytest tests/ -v
   ```
4. Commit with a descriptive message: `git commit -m "Add feature X"`
5. Push and open a Pull Request.

## Code Style

- Follow [PEP 8](https://pep8.org/) conventions.
- Use type hints where practical.
- Add docstrings to public functions and classes.

## Adding Documents

To add new knowledge base documents:

1. Place `.txt` or `.md` files in the project root or a subdirectory.
2. Run the embedding script:
   ```bash
   python embed.py --file your_file.txt
   # or embed an entire directory
   python embed.py --dir ./docs
   ```

## Reporting Issues

- Use [GitHub Issues](https://github.com/danishsyed-dev/RAG-API/issues) to report bugs or request features.
- Include steps to reproduce, expected vs. actual behavior, and your environment details.

## License

By contributing, you agree that your contributions will be licensed under the [MIT License](LICENSE).
