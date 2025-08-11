# Overview

This project is a Telegram bot that converts SVG files into TGS (Telegram Animated Stickers) format. The bot provides a complete solution for creating Telegram stickers from SVG files, featuring batch processing capabilities, comprehensive admin controls, and user management functionality. The application is designed to run as a long-running service and can be deployed on cloud platforms like Render.

## Recent Changes (2025-08-11)
- FIXED: SVG to TGS conversion now working perfectly using lottie_convert.py
- FIXED: Duplicate file processing issue resolved with improved batch logic
- IMPROVED: Batch processing for multiple files - single "Please wait..." message
- IMPLEMENTED: Complete file validation and error handling
- VERIFIED: TGS files generate correctly (3-5KB files with valid gzip headers)
- STATUS: Bot fully operational and ready for production deployment
- NOTE: Conversion creates valid TGS files suitable for Telegram stickers

# User Preferences

Preferred communication style: Simple, everyday language.

# System Architecture

## Bot Framework
The application is built using the python-telegram-bot library, following an asynchronous architecture with handlers for different types of user interactions. The bot uses a command-based interface for admin functions and message handlers for file processing.

## File Processing Pipeline
The core conversion functionality uses a multi-stage pipeline:
- SVG file validation (size, dimensions, format)
- SVG to Lottie animation object conversion using the lottie library
- TGS export with gzip compression
- Temporary file management with automatic cleanup

## Database Design
The system uses SQLite as the primary database with a simple schema focused on user management:
- User tracking and statistics
- Ban/unban functionality for admin control
- Persistent storage for user preferences and activity logs

## Admin System
A role-based admin system provides:
- User management commands (ban/unban users)
- Broadcasting capabilities for sending messages to all users
- Statistics tracking and reporting
- Administrative controls accessible only to designated admin users

## File Handling Strategy
The bot implements secure file handling with:
- Temporary file storage during processing
- File size and format validation before processing
- Automatic cleanup of temporary files after conversion
- Support for batch processing of multiple files

## Error Handling and Logging
Comprehensive error handling includes:
- Structured logging for debugging and monitoring
- User-friendly error messages for common issues
- Graceful degradation when conversion fails
- Exception handling for network and file system operations

# External Dependencies

## Core Libraries
- **python-telegram-bot**: Main framework for Telegram bot functionality
- **lottie[all]**: SVG to Lottie animation conversion
- **Pillow (PIL)**: Image processing and validation
- **cairosvg**: SVG rendering and processing support

## System Requirements
- **SQLite**: Database for user management and statistics
- **Python 3.8+**: Runtime environment
- **Telegram Bot API**: External service for bot communication

## Environment Configuration
- **BOT_TOKEN**: Telegram bot authentication token
- **ADMIN_ID**: Telegram user ID for administrative access
- **DATABASE_PATH**: SQLite database file location
- **ENVIRONMENT**: Deployment environment configuration

## Cloud Platform Integration
The bot is designed for deployment on cloud platforms like Render, with:
- Environment variable configuration
- Persistent database storage
- Long-running service architecture
- Health check and monitoring capabilities