# Contributing to SVG to TGS Converter Bot

Thank you for your interest in contributing to this project! This document provides guidelines for contributors.

## Getting Started

### Prerequisites
- Python 3.8 or higher
- Git
- Telegram Bot Token (for testing)
- Basic knowledge of Python and Telegram Bot API

### Development Setup

1. **Fork and clone the repository:**
   ```bash
   git clone https://github.com/your-username/svg-to-tgs-bot.git
   cd svg-to-tgs-bot
   ```

2. **Set up environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env with your bot token and admin ID
   ```

3. **Install dependencies:**
   ```bash
   pip install python-telegram-bot lottie[all] pillow cairosvg
   ```

4. **Run the bot:**
   ```bash
   python main.py
   ```

## Code Standards

### Python Style
- Follow PEP 8 style guidelines
- Use type hints where appropriate
- Write descriptive function and variable names
- Add docstrings for all classes and functions

### Code Structure
- Keep all files in the root directory (no subfolders)
- Use async/await for asynchronous operations
- Handle errors gracefully with proper logging
- Clean up temporary files after use

### Testing
- Test your changes thoroughly with actual SVG files
- Verify bot commands work as expected
- Check error handling with invalid inputs
- Test batch processing with multiple files

## Contribution Process

### 1. Issues
- Check existing issues before creating new ones
- Use issue templates when available
- Provide clear reproduction steps for bugs
- Include system information (Python version, OS, etc.)

### 2. Pull Requests
- Create a feature branch from `main`
- Write clear commit messages
- Include tests for new functionality
- Update documentation if needed
- Ensure code passes all checks

### 3. Review Process
- All PRs require review before merging
- Address feedback promptly
- Keep PRs focused and reasonably sized
- Rebase on main if conflicts arise

## Areas for Contribution

### High Priority
- Improve SVG parsing and validation
- Better TGS conversion quality
- Error handling and user feedback
- Performance optimizations

### Medium Priority
- Additional admin features
- Better logging and monitoring
- Code documentation improvements
- Test coverage expansion

### Low Priority
- UI/UX enhancements
- Additional file format support
- Docker improvements
- Deployment optimizations

## Bug Reports

When reporting bugs, include:
- Python version and OS
- Bot configuration (without sensitive data)
- Steps to reproduce the issue
- Expected vs actual behavior
- Error logs if available
- Sample SVG files (if relevant)

## Feature Requests

For new features, provide:
- Clear use case description
- Detailed requirements
- Implementation suggestions
- Potential impacts on existing functionality

## Security

- Never commit API keys or tokens
- Report security vulnerabilities privately
- Use environment variables for sensitive data
- Follow secure coding practices

## Documentation

### Code Documentation
- Add docstrings for all public functions
- Comment complex logic clearly
- Update README.md for user-facing changes
- Keep technical documentation current

### User Documentation
- Include usage examples
- Explain configuration options
- Document troubleshooting steps
- Provide deployment guides

## Community Guidelines

### Be Respectful
- Use welcoming and inclusive language
- Respect different viewpoints and experiences
- Focus on constructive feedback
- Help newcomers learn and contribute

### Communication
- Use clear, concise language
- Ask questions when uncertain
- Provide context for suggestions
- Be patient with review process

## Recognition

Contributors will be:
- Listed in the project's contributor list
- Credited in release notes
- Acknowledged for significant contributions
- Invited to participate in project decisions

## Getting Help

- Check the README.md first
- Search existing issues and discussions
- Ask questions in GitHub issues
- Join community discussions
- Reach out to maintainers if needed

## License

By contributing to this project, you agree that your contributions will be licensed under the same MIT License that covers the project.

---

Thank you for contributing to SVG to TGS Converter Bot! Your help makes this project better for everyone.